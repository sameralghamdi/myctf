"""Email sign-in codes and emailed password-reset links (memory mail backend)."""
from __future__ import annotations

import re

import pytest

from app import create_app, mailer
from app.config import TestConfig
from app.labs import base as labbase  # noqa: F401  (keeps fixture parity)


class OtpConfig(TestConfig):
    LOGIN_EMAIL_OTP = "1"
    PUBLIC_URL = "https://ctf.example.test"


@pytest.fixture()
def otp_client():
    mailer.OUTBOX.clear()
    yield create_app(OtpConfig).test_client()
    mailer.OUTBOX.clear()


def _code(msg) -> str:
    return re.search(r"\b(\d{6})\b", msg.get_body(("plain",)).get_content()).group(1)


def _register(client, name="otpuser"):
    return client.post("/api/auth/register", json={
        "username": name, "email": f"{name}@mail.test", "password": "Sup3rSecret!x9"})


def _login(client, name="otpuser", otp=None):
    body = {"username": name, "password": "Sup3rSecret!x9"}
    if otp is not None:
        body["otp"] = otp
    return client.post("/api/auth/login", json=body)


def test_register_does_not_sign_in_until_the_emailed_code_is_entered(otp_client):
    r = _register(otp_client)
    assert r.status_code == 201 and r.get_json()["verify_required"] is True
    assert "token" not in r.get_json() and "myctf_token" not in r.headers.get("Set-Cookie", "")
    assert otp_client.get("/api/session").get_json()["user"] is None

    r = _login(otp_client)
    assert r.status_code == 401
    body = r.get_json()
    assert body["error"] == "email_otp_required" and body["email_hint"].endswith("@mail.test")
    assert "otpuser@" not in body["email_hint"]
    assert len(mailer.OUTBOX) == 1 and mailer.OUTBOX[0]["To"] == "otpuser@mail.test"

    r = _login(otp_client, otp=_code(mailer.OUTBOX[0]))
    assert r.status_code == 200 and r.get_json()["user"]["email_verified"] is True
    assert otp_client.get("/api/session").get_json()["user"]["username"] == "otpuser"


def test_wrong_codes_expire_the_code_after_five_tries(otp_client):
    _register(otp_client)
    _login(otp_client)
    good = _code(mailer.OUTBOX[-1])
    wrong = "000000" if good != "000000" else "111111"
    for _ in range(5):
        r = _login(otp_client, otp=wrong)
        assert r.status_code == 401 and r.get_json()["code"] == "code_wrong"
    # Even the right code is now refused: a new one must be requested.
    r = _login(otp_client, otp=good)
    assert r.status_code == 401 and r.get_json()["code"] == "code_expired"


def test_a_new_code_replaces_the_old_one_and_codes_are_single_use(otp_client):
    _register(otp_client)
    _login(otp_client)
    first = _code(mailer.OUTBOX[-1])
    _login(otp_client)  # "Resend code"
    second = _code(mailer.OUTBOX[-1])
    if first != second:
        assert _login(otp_client, otp=first).status_code == 401
    assert _login(otp_client, otp=second).status_code == 200
    assert _login(otp_client, otp=second).status_code == 401  # already used


def test_wrong_password_never_sends_a_code(otp_client):
    _register(otp_client)
    r = otp_client.post("/api/auth/login", json={"username": "otpuser", "password": "nope"})
    assert r.status_code == 401 and r.get_json()["error"] == "Invalid credentials."
    assert mailer.OUTBOX == []


def test_code_sends_are_rate_limited(otp_client):
    _register(otp_client)
    for _ in range(5):
        assert _login(otp_client).status_code == 401
    assert _login(otp_client).status_code == 429
    assert len(mailer.OUTBOX) == 5


def test_forgot_password_emails_a_working_link(otp_client):
    _register(otp_client)
    r = otp_client.post("/api/auth/password/forgot", json={"email": "otpuser@mail.test"})
    assert r.status_code == 200
    text = mailer.OUTBOX[-1].get_body(("plain",)).get_content()
    link = re.search(r"https://ctf\.example\.test/reset/(\S+)", text)
    assert link, text
    r = otp_client.post("/api/auth/password/reset", json={"token": link.group(1), "password": "N3w-Passw0rd!"})
    assert r.status_code == 200
    r = otp_client.post("/api/auth/login", json={"username": "otpuser", "password": "N3w-Passw0rd!"})
    assert r.get_json()["error"] == "email_otp_required"  # new password works, code still required


def test_forgot_password_unknown_email_sends_nothing_and_says_the_same(otp_client):
    known = None
    _register(otp_client)
    r1 = otp_client.post("/api/auth/password/forgot", json={"email": "nobody@mail.test"}).get_json()
    assert mailer.OUTBOX == []
    known = otp_client.post("/api/auth/password/forgot", json={"email": "otpuser@mail.test"}).get_json()
    assert r1["message"] == known["message"]


def test_authenticator_users_are_not_asked_for_an_email_code(otp_client):
    from app import models
    from app.security import new_totp_secret
    _register(otp_client)
    with otp_client.application.app_context():
        user = models.get_user_by_username("otpuser")
        db = models.get_db()
        db.execute("UPDATE users SET totp_secret=? WHERE id=?", (new_totp_secret(), user["id"]))
        db.commit()
    assert _login(otp_client).get_json()["error"] == "otp_required"
    assert mailer.OUTBOX == []


def test_email_codes_are_off_by_default_without_smtp(client):
    r = client.post("/api/auth/register", json={
        "username": "plain1", "email": "plain1@mail.test", "password": "Sup3rSecret!x9"})
    assert r.status_code == 201 and r.get_json()["token"]


def test_set_email_cli(app):
    from app import models
    runner = app.test_cli_runner()
    assert runner.invoke(args=["set-email", "admin", "boss@mail.test"]).exit_code == 0
    with app.app_context():
        assert models.get_user_by_username("admin")["email"] == "boss@mail.test"
    assert runner.invoke(args=["set-email", "admin", "not-an-email"]).exit_code != 0
