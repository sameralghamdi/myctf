"""Regression tests for the security hardening pass."""
from __future__ import annotations

import pytest

from app import create_app, limiter, models
from app.config import TestConfig
from conftest import auth_headers, register

PW = "Sup3rSecret!x9"


def _login(client, username, password=PW, **extra):
    return client.post("/api/auth/login", json={"username": username,
                                                "password": password, **extra})


# ------------------------------------------------------------ CSRF / headers
def test_cross_site_origin_is_blocked(client):
    r = client.post("/api/auth/login", json={"username": "x", "password": "y"},
                    headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_null_origin_is_blocked(client):
    r = client.post("/api/auth/login", json={"username": "x", "password": "y"},
                    headers={"Origin": "null"})
    assert r.status_code == 403


def test_same_origin_and_no_origin_allowed(client):
    assert _login(client, "nobody").status_code == 401
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "y"},
                    headers={"Origin": "http://localhost"})
    assert r.status_code == 401  # reached the handler, not blocked


def test_configured_origin_allowed():
    class Cfg(TestConfig):
        ALLOWED_ORIGINS = ["https://ctf.example.com"]
    c = create_app(Cfg).test_client()
    ok = c.post("/api/auth/login", json={"username": "x", "password": "y"},
                headers={"Origin": "https://ctf.example.com"})
    assert ok.status_code == 401
    bad = c.post("/api/auth/login", json={"username": "x", "password": "y"},
                 headers={"Origin": "https://ctf.example.com.evil.io"})
    assert bad.status_code == 403


def test_security_headers_on_api(client):
    r = client.get("/api/public")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert r.headers["Referrer-Policy"] == "no-referrer"


def test_hsts_only_when_secure():
    class Cfg(TestConfig):
        COOKIE_SECURE = True
    r = create_app(Cfg).test_client().get("/healthz")
    assert "max-age" in r.headers["Strict-Transport-Security"]


def test_oversized_body_rejected(client):
    r = client.post("/api/auth/login", data=b"x" * (2 * 1024 * 1024),
                    content_type="application/json")
    assert r.status_code == 413


# ------------------------------------------------------- input hardening
@pytest.mark.parametrize("body", [[], "str", 5, {"username": ["a"], "password": {"x": 1}}])
def test_malformed_json_never_500s(client, body):
    for path in ("/api/auth/login", "/api/auth/register", "/api/auth/password/forgot"):
        r = client.post(path, json=body)
        assert r.status_code < 500, (path, body)


def test_flag_must_be_short_text(client):
    _, tok = register(client)
    h = auth_headers(tok)
    slug = client.get("/api/challenges", headers=h).get_json()[0]["slug"]
    assert client.post(f"/api/challenges/{slug}/submit", json={"flag": {"a": 1}},
                       headers=h).status_code == 400
    assert client.post(f"/api/challenges/{slug}/submit", json={"flag": "A" * 500},
                       headers=h).status_code == 400
    assert client.post(f"/api/challenges/{slug}/submit", json=["x"],
                       headers=h).status_code == 400


def test_long_password_not_hashed(client):
    r = _login(client, "admin", "A" * 5000)
    assert r.status_code == 401
    r = client.post("/api/auth/register", json={
        "username": "longpw", "email": "l@test.local", "password": "Aa1!" * 100})
    assert r.status_code == 400


def test_username_case_insensitive_unique(client):
    register(client, "Alice")
    r = client.post("/api/auth/register", json={
        "username": "alice", "email": "other@test.local", "password": PW})
    assert r.status_code == 400
    assert _login(client, "ALICE").status_code == 200


def test_redirect_target_blocks_control_chars(client):
    register(client, "redir")
    r = client.post("/login?next=/%09/evil.example",
                    data={"username": "redir", "password": PW})
    assert r.status_code == 302
    assert "evil.example" not in r.headers["Location"]


# ------------------------------------------------------- rate limiting
def test_register_is_rate_limited(client):
    codes = [client.post("/api/auth/register", json={
        "username": f"mass{i}", "email": f"mass{i}@t.local", "password": PW}).status_code
        for i in range(23)]
    assert codes[:20] == [201] * 20
    assert 429 in codes[20:]


def test_forgot_password_is_rate_limited(client):
    codes = [client.post("/api/auth/password/forgot",
                         json={"email": "a@b.co"}).status_code for _ in range(8)]
    assert codes[0] == 200 and 429 in codes


def test_wrong_otp_locks_out(client):
    from app.security import new_totp_secret, totp_now
    _, tok = register(client, "otpuser")
    secret = new_totp_secret()
    assert client.post("/api/auth/2fa/confirm", headers=auth_headers(tok),
                       json={"secret": secret, "otp": totp_now(secret)}).status_code == 200
    seen = [_login(client, "otpuser", otp="000000").status_code for _ in range(6)]
    assert seen[:5] == [401] * 5 and seen[5] == 429
    # even the right code is refused during the lockout
    assert _login(client, "otpuser", otp=totp_now(secret)).status_code == 429


def test_limiter_memory_is_bounded(monkeypatch):
    monkeypatch.setattr(limiter, "_MAX_KEYS", 50)
    for i in range(200):
        limiter.allow(f"k{i}", 1, 0)   # window 0 -> instantly stale
    import time
    monkeypatch.setattr(time, "time", lambda: 10**10)
    limiter.allow("trigger", 1, 60)
    assert len(limiter._HITS) <= 51


# ------------------------------------------------------- sessions / 2FA
def test_password_reset_signs_out_other_sessions(client):
    _, tok = register(client, "victim")
    assert client.get("/api/auth/me", headers=auth_headers(tok)).status_code == 200
    link = client.post("/api/auth/password/forgot",
                       json={"email": "victim@test.local"}).get_json()["reset_link"]
    token = link.rsplit("/", 1)[1]
    r = client.post("/api/auth/password/reset",
                    json={"token": token, "password": "BrandN3w!Passw0rd"})
    assert r.status_code == 200
    assert client.get("/api/auth/me", headers=auth_headers(tok)).status_code == 401
    assert _login(client, "victim", "BrandN3w!Passw0rd").status_code == 200


def test_disabling_2fa_needs_password_and_code(client):
    from app.security import new_totp_secret, totp_now
    _, tok = register(client, "twofa")
    h = auth_headers(tok)
    secret = new_totp_secret()
    client.post("/api/auth/2fa/confirm", headers=h,
                json={"secret": secret, "otp": totp_now(secret)})
    assert client.post("/api/auth/2fa/disable", headers=h, json={}).status_code == 403
    assert client.post("/api/auth/2fa/disable", headers=h,
                       json={"password": PW}).status_code == 403
    assert client.post("/api/auth/2fa/disable", headers=h,
                       json={"password": PW, "otp": totp_now(secret)}).status_code == 200


def test_2fa_confirm_rejects_junk_secret(client):
    _, tok = register(client)
    r = client.post("/api/auth/2fa/confirm", headers=auth_headers(tok),
                    json={"secret": "not base32!", "otp": "123456"})
    assert r.status_code == 400


# ------------------------------------------------------- drafts / admin
def _draft(app):
    with app.app_context():
        row = models.get_db().execute(
            "SELECT id, slug, lab_kind FROM challenges WHERE lab_kind!='static' LIMIT 1"
        ).fetchone()
        models.set_challenge_published(row["id"], False)
        return row["slug"]


def test_drafts_are_not_playable(app, client):
    slug = _draft(app)
    _, tok = register(client)
    h = auth_headers(tok)
    assert client.post(f"/api/challenges/{slug}/lab/start", headers=h).status_code == 404
    assert client.post(f"/api/challenges/{slug}/submit", json={"flag": "MYCTF{x}"},
                       headers=h).status_code == 404
    assert client.post(f"/api/challenges/{slug}/hints/1", headers=h).status_code == 404


def test_admin_can_still_test_drafts(app, client):
    slug = _draft(app)
    tok = _login(client, "admin", "ChangeMe_Admin!123").get_json()["token"]
    r = client.post(f"/api/challenges/{slug}/lab/start", headers=auth_headers(tok))
    assert r.status_code == 200


def test_admin_cannot_change_own_role(client):
    tok = _login(client, "admin", "ChangeMe_Admin!123").get_json()["token"]
    h = auth_headers(tok)
    me = client.get("/api/auth/me", headers=h).get_json()
    r = client.post(f"/admin/api/users/{me['id']}/role", headers=h,
                    json={"role": "student"})
    assert r.status_code == 400


@pytest.mark.parametrize("patch", [
    {"points": -5}, {"points": 10**9}, {"points": True},
    {"hints": [{"level": 1, "body": "x", "cost": -100}]},
    {"references": [{"title": "t", "url": "javascript:alert(1)"}]},
    {"objectives": "not a list"},
])
def test_manifest_rejects_unsafe_values(client, patch):
    from app.manifest import ManifestError, validate
    base = {"slug": "demo-chal", "name": "Demo", "category": "web",
            "difficulty": "easy", "lab_kind": "static", "flag": "MYCTF{demo}"}
    validate(base)  # baseline is valid
    with pytest.raises(ManifestError):
        validate({**base, **patch})


def test_manifest_non_object_rejected(client):
    tok = _login(client, "admin", "ChangeMe_Admin!123").get_json()["token"]
    r = client.post("/admin/api/challenges/validate", headers=auth_headers(tok),
                    json=["nope"])
    assert r.status_code == 400


# ------------------------------------------------------- lab isolation
def test_lab_responses_have_headers(app, client):
    _, tok = register(client)
    h = auth_headers(tok)
    slug = next(c["slug"] for c in client.get("/api/challenges", headers=h).get_json()
                if c["has_lab"])
    url = client.post(f"/api/challenges/{slug}/lab/start", headers=h).get_json()["url"]
    r = client.get(url, headers=h)
    assert r.status_code == 200
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["X-Frame-Options"] == "SAMEORIGIN"


def test_login_timing_path_runs_for_unknown_user(client, monkeypatch):
    from app.auth import routes
    calls = []
    monkeypatch.setattr(routes, "verify_password",
                        lambda pw, stored: calls.append(1) or False)
    assert _login(client, "no-such-user").status_code == 401
    assert calls, "a dummy hash check must run so timing doesn't reveal usernames"


# ------------------------------------------------------- admin CTF form API
def _admin(client):
    return auth_headers(_login(client, "admin", "ChangeMe_Admin!123").get_json()["token"])


FORM = {"slug": "form-made", "name": "Form Made", "category": "pwn",
        "category_name": "Pwn", "difficulty": "medium", "points": 250,
        "lab_kind": "static", "flag": "MYCTF{from_the_form}",
        "description": "# Title\nSome **markdown**.",
        "target_url": "https://target.example.com/app",
        "hints": [{"level": 1, "cost": 10, "body": "look closer"}],
        "published": True, "create_only": True}


def test_admin_form_creates_playable_challenge(client):
    h = _admin(client)
    assert client.post("/admin/api/challenges/publish", headers=h, json=FORM).status_code == 200
    detail = client.get("/api/challenges/form-made", headers=h).get_json()
    assert detail["target_url"] == "https://target.example.com/app"
    assert detail["points"] == 250 and detail["category_name"] == "Pwn"
    assert "flag" not in detail and "flag_hash" not in detail
    ok = client.post("/api/challenges/form-made/submit", headers=h,
                     json={"flag": "MYCTF{from_the_form}"})
    assert ok.status_code == 200
    assert {"slug": "pwn", "name": "Pwn"} in client.get(
        "/admin/api/categories", headers=h).get_json()


def test_admin_form_cannot_overwrite_existing_slug(client):
    h = _admin(client)
    client.post("/admin/api/challenges/publish", headers=h, json=FORM)
    again = client.post("/admin/api/challenges/publish", headers=h,
                        json={**FORM, "flag": "MYCTF{hijacked}"})
    assert again.status_code == 409


def test_students_cannot_create_challenges(client):
    _, tok = register(client)
    h = auth_headers(tok)
    assert client.post("/admin/api/challenges/publish", headers=h, json=FORM).status_code == 403
    assert client.get("/admin/api/categories", headers=h).status_code == 403
    anonymous = client.application.test_client()   # no session cookie
    assert anonymous.post("/admin/api/challenges/publish", json=FORM).status_code == 401


@pytest.mark.parametrize("url", ["javascript:alert(1)", "ftp://x.y", "http://a b", 5])
def test_target_url_must_be_http(client, url):
    from app.manifest import ManifestError, validate
    with pytest.raises(ManifestError):
        validate({**FORM, "target_url": url})


def test_draft_detail_visible_to_admin_only(client):
    h = _admin(client)
    client.post("/admin/api/challenges/publish", headers=h, json={**FORM, "published": False})
    assert client.get("/api/challenges/form-made", headers=h).status_code == 200
    student = client.application.test_client()
    _, tok = register(student)
    assert student.get("/api/challenges/form-made", headers=auth_headers(tok)).status_code == 404


# ------------------------------------------------------- production hardening
def test_no_cors_headers_ever(client):
    """The API is same-origin only: it must never opt in to cross-origin reads."""
    evil = {"Origin": "https://evil.example"}
    preflight = client.open("/api/auth/login", method="OPTIONS", headers={
        **evil, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    for r in (preflight, client.get("/api/public", headers=evil),
              client.get("/api/session", headers=evil)):
        assert not [h for h in r.headers.keys() if h.lower().startswith("access-control-")]


def test_global_rate_limit():
    class Cfg(TestConfig):
        RATE_LIMIT_GLOBAL = 5
    c = create_app(Cfg).test_client()
    codes = [c.get("/api/public").status_code for _ in range(7)]
    assert codes[:5] == [200] * 5 and codes[5:] == [429, 429]
    assert c.get("/healthz").status_code == 200          # health checks are exempt
    assert c.get("/api/public").headers["Retry-After"] == "60"


def test_admin_password_is_random_when_unset(capsys):
    class Cfg(TestConfig):
        SEED_ADMIN_PASSWORD = None
    c = create_app(Cfg).test_client()
    printed = capsys.readouterr().err
    password = printed.split("password:")[1].split()[0]
    assert len(password) >= 16
    assert _login(c, "admin", "ChangeMe_Admin!123").status_code == 401
    assert _login(c, "admin", password).status_code == 200


def test_no_demo_credentials_in_pages(client):
    html = client.get("/login").get_data(as_text=True)
    assert "ChangeMe" not in html and "Demo admin" not in html
