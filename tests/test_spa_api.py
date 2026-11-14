"""API surface used by the React frontend + public-deployment hardening."""
from __future__ import annotations

import pytest

from app import create_app
from app.config import TestConfig
from conftest import register

ADMIN = {"username": "admin", "password": "ChangeMe_Admin!123"}


def _cookie_login(client, creds):
    r = client.post("/api/auth/login", json=creds)
    assert r.status_code == 200
    return r


# ------------------------------------------------------------ cookie sessions
def test_json_login_sets_httponly_cookie_and_session_works(client):
    username, _ = register(client, "spauser")
    client.delete_cookie("myctf_token")
    r = _cookie_login(client, {"username": username, "password": "Sup3rSecret!x9"})
    cookie = r.headers.get("Set-Cookie", "")
    assert "myctf_token=" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie

    s = client.get("/api/session").get_json()
    assert s["user"]["username"] == username
    assert s["score"] == 0

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/session").get_json() == {"user": None}


def test_session_is_200_when_logged_out(client):
    r = client.get("/api/session")
    assert r.status_code == 200 and r.get_json() == {"user": None}


def test_register_sets_cookie(client):
    r = client.post("/api/auth/register", json={
        "username": "freshie", "email": "freshie@test.local",
        "password": "Sup3rSecret!x9"})
    assert r.status_code == 201
    assert "myctf_token=" in r.headers.get("Set-Cookie", "")
    assert client.get("/api/session").get_json()["user"]["username"] == "freshie"


# --------------------------------------------------- public-deployment hardening
class ProdLike(TestConfig):
    EXPOSE_DEV_LINKS = False
    COOKIE_SECURE = True
    ORIGIN_SECRET = "s3cret-origin"


@pytest.fixture()
def prod_client():
    return create_app(ProdLike).test_client()


def test_reset_and_verify_links_not_leaked_by_default(prod_client):
    h = {"X-Origin-Secret": "s3cret-origin"}
    r = prod_client.post("/api/auth/register", headers=h, json={
        "username": "victim", "email": "victim@test.local",
        "password": "Sup3rSecret!x9"})
    assert r.status_code == 201 and "verify_link" not in r.get_json()
    f = prod_client.post("/api/auth/password/forgot", headers=h,
                         json={"email": "victim@test.local"})
    assert f.status_code == 200
    assert "reset_link" not in f.get_json()


def test_secure_cookie_flag_follows_config(prod_client):
    h = {"X-Origin-Secret": "s3cret-origin"}
    r = prod_client.post("/api/auth/login", headers=h, json=ADMIN)
    assert "Secure" in r.headers["Set-Cookie"]


def test_origin_secret_required(prod_client):
    assert prod_client.get("/api/public").status_code == 403
    assert prod_client.get("/api/public",
                           headers={"X-Origin-Secret": "wrong"}).status_code == 403
    assert prod_client.get("/api/public",
                           headers={"X-Origin-Secret": "s3cret-origin"}).status_code == 200
    # health check stays open for the container orchestrator
    assert prod_client.get("/healthz").status_code == 200


def test_real_client_ip_taken_from_trusted_proxy_header():
    app = create_app(ProdLike)
    c = app.test_client()
    h = {"X-Origin-Secret": "s3cret-origin", "X-Client-IP": "203.0.113.9"}
    assert c.post("/api/auth/login", headers=h,
                  json={"username": "admin", "password": "wrong"}).status_code == 401
    with app.app_context():
        from app import models
        row = models.get_db().execute(
            "SELECT ip FROM audit_logs WHERE action='login_fail'").fetchone()
        assert row["ip"] == "203.0.113.9"


def test_client_ip_header_ignored_without_secret(client):
    # No ORIGIN_SECRET configured -> the header is just an untrusted request header.
    client.post("/api/auth/login", headers={"X-Client-IP": "198.51.100.7"},
                json={"username": "admin", "password": "wrong"})
    from app import models
    with client.application.app_context():
        row = models.get_db().execute(
            "SELECT ip FROM audit_logs WHERE action='login_fail'").fetchone()
        assert row["ip"] != "198.51.100.7"


def test_login_rate_limited_after_failures(client):
    for _ in range(10):
        assert client.post("/api/auth/login",
                           json={"username": "admin", "password": "nope"}).status_code == 401
    # Even the right password is refused while locked out.
    assert client.post("/api/auth/login", json=ADMIN).status_code == 429


def test_login_next_redirect_is_same_site_only(client):
    for evil in ("https://evil.example", "//evil.example", "/\\evil.example"):
        r = client.post(f"/login?next={evil}", data=ADMIN)
        assert r.status_code == 302
        assert r.headers["Location"] == "/dashboard", evil
        client.post("/logout")
    r = client.post("/login?next=/challenges", data=ADMIN)
    assert r.headers["Location"] == "/challenges"


# ------------------------------------------------------------ new endpoints
def test_public_endpoint_needs_no_auth(client):
    d = client.get("/api/public").get_json()
    assert set(d["stats"]) == {"users", "challenges", "solves", "categories"}
    assert "static" in d["live_kinds"] or d["live_kinds"]


def test_profile_paths_achievements_shapes(client):
    register(client, "shapeuser")
    p = client.get("/api/profile").get_json()
    assert p["user"]["username"] == "shapeuser"
    assert {"score", "rank", "solves", "skills", "achievements"} <= set(p)
    assert any(a["slug"] == "welcome" for a in p["achievements"])

    paths = client.get("/api/paths").get_json()
    assert paths and {"slug", "name", "level", "done", "total", "items"} <= set(paths[0])

    ach = client.get("/api/achievements").get_json()
    assert ach and {"slug", "name", "description", "earned"} <= set(ach[0])
    assert any(a["earned"] for a in ach)


def test_challenge_list_has_status(client):
    register(client, "statususer")
    rows = client.get("/api/challenges").get_json()
    assert rows and all(r["status"] in {"new", "progress", "solved"} for r in rows)


def test_profile_requires_login(client):
    for path in ("/api/profile", "/api/paths", "/api/achievements"):
        assert client.get(path).status_code == 401


def test_admin_endpoints_for_spa(client):
    _cookie_login(client, ADMIN)
    ov = client.get("/admin/api/overview").get_json()
    assert "stats" in ov and any(u["username"] == "admin" for u in ov["users"])
    chals = client.get("/admin/api/challenges").get_json()
    assert chals and {"id", "slug", "published"} <= set(chals[0])

    client.post("/api/auth/logout")
    register(client, "plainuser")
    assert client.get("/admin/api/overview",
                      headers={"Accept": "application/json"}).status_code == 403
