"""Authentication, RBAC and session management tests."""
from __future__ import annotations

from conftest import auth_headers, register


def test_health(client):
    assert client.get("/healthz").get_json()["status"] == "ok"


def test_register_and_me(client):
    username, token = register(client)
    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.get_json()["username"] == username
    assert me.get_json()["role"] == "student"


def test_register_rejects_weak_password(client):
    r = client.post("/api/auth/register", json={
        "username": "weakling", "email": "w@test.local", "password": "short"})
    assert r.status_code == 400
    assert "Password" in r.get_json()["error"]


def test_register_rejects_duplicate(client):
    register(client, "dupe")
    r = client.post("/api/auth/register", json={
        "username": "dupe", "email": "other@test.local", "password": "Sup3rSecret!x9"})
    assert r.status_code == 400


def test_login_and_logout_revokes_session(client):
    username, _ = register(client, "loginuser")
    r = client.post("/api/auth/login",
                    json={"username": "loginuser", "password": "Sup3rSecret!x9"})
    assert r.status_code == 200
    token = r.get_json()["token"]
    assert client.get("/api/auth/me", headers=auth_headers(token)).status_code == 200
    # logout revokes the server-side session -> the token stops working
    assert client.post("/api/auth/logout", headers=auth_headers(token)).status_code == 200
    assert client.get("/api/auth/me", headers=auth_headers(token)).status_code == 401


def test_bad_password_rejected(client):
    register(client, "pwuser")
    r = client.post("/api/auth/login",
                    json={"username": "pwuser", "password": "wrong-password-1"})
    assert r.status_code == 401


def test_unauthenticated_api_is_blocked(client):
    assert client.get("/api/challenges").status_code == 401


def test_student_cannot_reach_admin(client):
    _, token = register(client, "plainstudent")
    r = client.get("/admin/api/audit", headers=auth_headers(token))
    assert r.status_code == 403


def test_admin_can_reach_admin(client):
    r = client.post("/api/auth/login",
                    json={"username": "admin", "password": "ChangeMe_Admin!123"})
    assert r.status_code == 200
    token = r.get_json()["token"]
    assert client.get("/admin/api/audit", headers=auth_headers(token)).status_code == 200


def test_password_reset_flow(client):
    register(client, "resetme")
    forgot = client.post("/api/auth/password/forgot", json={"email": "resetme@test.local"})
    link = forgot.get_json()["reset_link"]
    assert link
    token = link.rstrip("/").split("/")[-1]
    r = client.post("/api/auth/password/reset",
                    json={"token": token, "password": "BrandN3w!pass9"})
    assert r.status_code == 200
    # old password no longer works, new one does
    assert client.post("/api/auth/login",
                       json={"username": "resetme",
                             "password": "Sup3rSecret!x9"}).status_code == 401
    assert client.post("/api/auth/login",
                       json={"username": "resetme",
                             "password": "BrandN3w!pass9"}).status_code == 200


def test_two_factor_enable_and_login(client):
    from app.security import totp_now
    username, token = register(client, "tfauser")
    enable = client.post("/api/auth/2fa/enable", headers=auth_headers(token))
    secret = enable.get_json()["secret"]
    code = totp_now(secret)
    confirm = client.post("/api/auth/2fa/confirm", headers=auth_headers(token),
                          json={"secret": secret, "otp": code})
    assert confirm.status_code == 200
    # login now requires the OTP
    r = client.post("/api/auth/login",
                    json={"username": "tfauser", "password": "Sup3rSecret!x9"})
    assert r.status_code == 401 and r.get_json()["error"] == "otp_required"
    r2 = client.post("/api/auth/login",
                     json={"username": "tfauser", "password": "Sup3rSecret!x9",
                           "otp": totp_now(secret)})
    assert r2.status_code == 200
