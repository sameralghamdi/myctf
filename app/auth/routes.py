"""Auth endpoints. JSON API under /api/auth/* plus server-rendered HTML pages.

Handlers accept form or JSON and respond accordingly, so the same logic backs the
browser UI and API clients/tests.
"""
from __future__ import annotations

import re

from flask import (Blueprint, current_app, g, jsonify, make_response, redirect,
                   render_template, request, url_for)

from .. import limiter, models
from ..security import (decode_token, hash_password, hash_token, issue_token,
                        new_id, new_totp_secret, totp_uri, totp_verify,
                        verify_password)
from . import COOKIE_NAME, current_user, login_required

bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _wants_json() -> bool:
    return (request.is_json or request.path.startswith("/api/")
            or "application/json" in request.headers.get("Accept", ""))


MAX_PASSWORD_LEN = 256   # PBKDF2 cost grows with input size; cap it (DoS guard)
_DUMMY_HASH: dict[int, str] = {}


def _payload() -> dict:
    if request.is_json:
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}
    return request.form.to_dict()


def _s(data: dict, key: str, limit: int = 256) -> str:
    """Read a string field. Non-strings (lists, numbers, objects) become ''."""
    value = data.get(key)
    return value.strip()[:limit] if isinstance(value, str) else ""


def _throttle(name: str, limit: int, window: int):
    """Return a 429 response if this client IP exceeded `limit` hits per window."""
    if not limiter.allow(f"{name}:{request.remote_addr or ''}", limit, window):
        return _fail("Too many requests. Please wait a bit and try again.", {}, 429)
    return None


def _dummy_verify(password: str) -> None:
    """Spend the same CPU as a real check so response time doesn't reveal which
    usernames exist."""
    iters = current_app.config["PBKDF2_ITERATIONS"]
    if iters not in _DUMMY_HASH:
        _DUMMY_HASH[iters] = hash_password("dummy-password-for-timing", iterations=iters)
    verify_password(password, _DUMMY_HASH[iters])


def _password_problem(pw: str) -> str | None:
    if len(pw) < 10:
        return "Password must be at least 10 characters."
    if len(pw) > MAX_PASSWORD_LEN:
        return f"Password must be at most {MAX_PASSWORD_LEN} characters."
    if pw.lower() in {"password12", "changeme12", "1234567890"}:
        return "Password is too common."
    classes = sum(bool(re.search(p, pw)) for p in
                  (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]"))
    if classes < 3:
        return "Use upper, lower, digits and symbols (at least 3 of 4)."
    return None


def _issue_login(user, remember: bool = True):
    session_id = new_id()
    ttl = current_app.config["SESSION_TTL"]
    models.create_session(session_id, user["id"], ttl,
                          user_agent=request.headers.get("User-Agent", "")[:200],
                          ip=request.remote_addr or "")
    models.set_last_login(user["id"])
    token = issue_token(user_id=user["id"], session_id=session_id,
                        secret=current_app.config["SECRET_KEY"], ttl=ttl)
    return token, ttl


# --------------------------------------------------------------- registration
@bp.post("/api/auth/register")
@bp.post("/register")
def register():
    blocked = _throttle("register", current_app.config["RATE_LIMIT_REGISTER"], 3600)
    if blocked:
        return blocked
    data = _payload()
    username = _s(data, "username", 64)
    email = _s(data, "email", 254).lower()
    password = data.get("password") if isinstance(data.get("password"), str) else ""

    errors = []
    if not USERNAME_RE.match(username):
        errors.append("Username must be 3–32 chars (letters, digits, . _ -).")
    if not EMAIL_RE.match(email):
        errors.append("Enter a valid email address.")
    pw_problem = _password_problem(password)
    if pw_problem:
        errors.append(pw_problem)
    if not errors:
        if models.get_user_by_username(username):
            errors.append("Username is taken.")
        if models.get_user_by_email(email):
            errors.append("Email is already registered.")

    if errors:
        if _wants_json():
            return jsonify({"error": "; ".join(errors)}), 400
        return render_template("auth/register.html", errors=errors, form=data), 400

    user_id = models.create_user(username, email, hash_password(
        password, iterations=current_app.config["PBKDF2_ITERATIONS"]))
    # Email verification token (no mailer in dev: surfaced for the flow to work).
    raw = new_id()
    models.create_onetime_token(user_id, "verify_email",
                                hash_token(raw, current_app.config["SECRET_KEY"]),
                                ttl=60 * 60 * 24)
    models.audit(user_id, "register", f"username={username}")
    models.grant_achievement(user_id, "welcome")

    user = models.get_user_by_id(user_id)
    token, ttl = _issue_login(user)
    verify_link = url_for("auth.verify_email", token=raw, _external=False)

    if _wants_json():
        body = {"ok": True, "token": token, "user": _public_user(user)}
        if current_app.config["EXPOSE_DEV_LINKS"]:
            body["verify_link"] = verify_link
        resp = make_response(jsonify(body), 201)
        _set_cookie(resp, token, ttl)
        return resp
    resp = make_response(redirect(url_for("core.dashboard")))
    _set_cookie(resp, token, ttl)
    return resp


# ---------------------------------------------------------------------- login
@bp.post("/api/auth/login")
@bp.post("/login")
def login():
    data = _payload()
    identifier = _s(data, "username", 254) or _s(data, "identifier", 254)
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    otp = _s(data, "otp", 16)

    limit = current_app.config["RATE_LIMIT_LOGIN"]
    window = current_app.config["RATE_LIMIT_WINDOW"]
    ip_key = f"login-ip:{request.remote_addr or ''}"
    id_key = f"login-id:{identifier.lower()}"
    # Block before checking the password so a locked-out attacker learns nothing.
    if not (limiter.peek(ip_key, limit * 3, window) and limiter.peek(id_key, limit, window)):
        return _fail("Too many attempts. Try again in a minute.", data, 429)

    user = models.get_user_by_login(identifier)
    if len(password) > MAX_PASSWORD_LEN:
        password = ""   # never hash an absurdly long input
    if user is None:
        _dummy_verify(password)
    ok = user is not None and verify_password(password, user["password_hash"])
    if not ok:
        limiter.allow(ip_key, limit * 3, window)
        limiter.allow(id_key, limit, window)
        models.audit(user["id"] if user else None, "login_fail",
                     f"id={identifier}", ip=request.remote_addr or "")
        return _fail("Invalid credentials.", data, 401)

    if user["totp_secret"]:
        if not otp:
            if _wants_json():
                return jsonify({"error": "otp_required"}), 401
            return render_template("auth/login.html", otp_required=True,
                                   form=data, errors=[]), 401
        # A 6-digit code is guessable, so wrong codes get a much tighter limit.
        otp_key = f"otp:{user['id']}"
        if not limiter.peek(otp_key, 5, 900):
            return _fail("Too many wrong codes. Try again in 15 minutes.", data, 429)
        if not totp_verify(user["totp_secret"], otp):
            limiter.allow(otp_key, 5, 900)
            models.audit(user["id"], "login_otp_fail", ip=request.remote_addr or "")
            return _fail("Invalid 2FA code.", data, 401)
        limiter.reset(otp_key)

    token, ttl = _issue_login(user)
    models.audit(user["id"], "login", ip=request.remote_addr or "")
    limiter.reset(id_key)
    if _wants_json():
        resp = make_response(jsonify({"ok": True, "token": token,
                                      "user": _public_user(user)}))
        _set_cookie(resp, token, ttl)
        return resp
    resp = make_response(redirect(_safe_next(request.args.get("next"))))
    _set_cookie(resp, token, ttl)
    return resp


@bp.post("/api/auth/logout")
@bp.post("/logout")
@login_required
def logout():
    token = (request.headers.get("Authorization", "")[7:].strip()
             or request.cookies.get(COOKIE_NAME))
    payload = decode_token(token, current_app.config["SECRET_KEY"]) if token else None
    if payload:
        models.revoke_session(payload.get("jti", ""))
        models.audit(int(payload["sub"]), "logout")
    if _wants_json():
        resp = make_response(jsonify({"ok": True}))
    else:
        resp = make_response(redirect(url_for("auth.login_page")))
    resp.delete_cookie(COOKIE_NAME)
    return resp


# ------------------------------------------------------------- email verify
@bp.get("/verify/<token>")
@bp.get("/api/auth/verify/<token>")
def verify_email(token: str):
    user_id = models.consume_onetime_token(
        "verify_email", hash_token(token, current_app.config["SECRET_KEY"]))
    if user_id:
        models.set_email_verified(user_id, True)
        models.audit(user_id, "email_verified")
        msg = "Email verified. You're all set."
    else:
        msg = "Invalid or expired verification link."
    if _wants_json():
        return jsonify({"ok": bool(user_id), "message": msg})
    return render_template("auth/message.html", title="Email verification", message=msg)


# ---------------------------------------------------------- password reset
@bp.get("/forgot")
def forgot_page():
    return render_template("auth/forgot.html")


@bp.post("/api/auth/password/forgot")
@bp.post("/forgot")
def forgot_password():
    blocked = _throttle("forgot", current_app.config["RATE_LIMIT_RESET"], 900)
    if blocked:
        return blocked
    data = _payload()
    email = _s(data, "email", 254).lower()
    user = models.get_user_by_email(email)
    link = None
    if user:  # do not reveal whether the email exists in the message
        raw = new_id()
        models.create_onetime_token(
            user["id"], "reset_password",
            hash_token(raw, current_app.config["SECRET_KEY"]), ttl=60 * 30)
        models.audit(user["id"], "password_reset_requested")
        link = url_for("auth.reset_password", token=raw, _external=False)
    # Dev only (MYCTF_EXPOSE_DEV_LINKS): surface the link because there is no
    # mailer yet. On a public site this MUST stay off or anyone could reset
    # anyone's password.
    if not current_app.config["EXPOSE_DEV_LINKS"]:
        link = None
    msg = "If that email exists, a reset link was sent."
    if _wants_json():
        body = {"ok": True, "message": msg}
        if current_app.config["EXPOSE_DEV_LINKS"]:
            body["reset_link"] = link
        return jsonify(body)
    return render_template("auth/message.html", title="Password reset",
                           message=msg, link=link)


@bp.route("/api/auth/password/reset", methods=["POST"])
@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token: str | None = None):
    if request.method == "GET":
        return render_template("auth/reset.html", token=token, errors=[])
    blocked = _throttle("reset", 20, 900)
    if blocked:
        return blocked
    data = _payload()
    token = token or _s(data, "token", 128)
    new_pw = data.get("password") if isinstance(data.get("password"), str) else ""
    problem = _password_problem(new_pw)
    if problem:
        return _reset_fail(token, problem)
    user_id = models.consume_onetime_token(
        "reset_password", hash_token(token or "", current_app.config["SECRET_KEY"]))
    if not user_id:
        return _reset_fail(token, "Invalid or expired reset link.")
    db = models.get_db()
    db.execute("UPDATE users SET password_hash=? WHERE id=?",
               (hash_password(new_pw, iterations=current_app.config["PBKDF2_ITERATIONS"]),
                user_id))
    db.commit()
    # A reset usually means the old password may be compromised: end every
    # session that was signed in with it.
    models.revoke_user_sessions(user_id)
    models.audit(user_id, "password_reset")
    if _wants_json():
        return jsonify({"ok": True, "message": "Password updated."})
    return render_template("auth/message.html", title="Password reset",
                           message="Password updated. You can sign in now.")


# -------------------------------------------------------------------- 2FA
@bp.post("/api/auth/2fa/enable")
@login_required
def enable_2fa():
    user = current_user()
    secret = new_totp_secret()
    # Nothing is stored yet: the secret only becomes active once the user proves
    # they can generate a valid code with it (see confirm_2fa).
    return jsonify({"secret": secret,
                    "otpauth_uri": totp_uri(secret, user["email"])})


@bp.post("/api/auth/2fa/confirm")
@login_required
def confirm_2fa():
    user = current_user()
    data = _payload()
    secret = _s(data, "secret", 64)
    code = _s(data, "otp", 16)
    if not limiter.allow(f"2fa-confirm:{user['id']}", 10, 900):
        return jsonify({"error": "Too many attempts. Try again later."}), 429
    if not re.fullmatch(r"[A-Z2-7]{16,64}", secret) or not totp_verify(secret, code):
        return jsonify({"error": "Invalid code for that secret."}), 400
    models.set_totp_secret(user["id"], secret)
    models.audit(user["id"], "2fa_enabled")
    return jsonify({"ok": True})


@bp.post("/api/auth/2fa/disable")
@login_required
def disable_2fa():
    """Turning 2FA off needs the password (and a current code), so a stolen
    session alone can't strip the account's second factor."""
    user = current_user()
    data = _payload()
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    if not limiter.allow(f"2fa-disable:{user['id']}", 5, 900):
        return jsonify({"error": "Too many attempts. Try again later."}), 429
    if len(password) > MAX_PASSWORD_LEN or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Password is incorrect."}), 403
    if user["totp_secret"] and not totp_verify(user["totp_secret"], _s(data, "otp", 16)):
        return jsonify({"error": "Invalid 2FA code."}), 403
    models.set_totp_secret(user["id"], None)
    models.audit(user["id"], "2fa_disabled")
    return jsonify({"ok": True})


@bp.get("/api/auth/me")
@login_required
def me():
    return jsonify(_public_user(current_user()))


@bp.get("/api/session")
def session_info():
    """Who am I? Always 200 so the SPA can boot without a 401 in the console."""
    user = current_user()
    if user is None:
        return jsonify({"user": None})
    return jsonify({"user": _public_user(user),
                    "score": models.user_score(user["id"]),
                    "rank": models.user_rank(user["id"]) or None})


# ----------------------------------------------------------------- HTML pages
@bp.get("/login")
def login_page():
    if current_user():
        return redirect(url_for("core.dashboard"))
    return render_template("auth/login.html", errors=[], form={}, otp_required=False)


@bp.get("/register")
def register_page():
    if current_user():
        return redirect(url_for("core.dashboard"))
    return render_template("auth/register.html", errors=[], form={})


# ------------------------------------------------------------------- helpers
def _public_user(user) -> dict:
    return {"id": user["id"], "username": user["username"], "email": user["email"],
            "display_name": user["display_name"] or user["username"],
            "role": user["role"], "email_verified": bool(user["email_verified"]),
            "two_factor": bool(user["totp_secret"])}


def _set_cookie(resp, token: str, ttl: int) -> None:
    resp.set_cookie(COOKIE_NAME, token, max_age=ttl, httponly=True,
                    samesite="Lax", secure=current_app.config["COOKIE_SECURE"])


def _safe_next(target: str | None) -> str:
    """Only allow same-site relative redirects (blocks open-redirect via ?next=)."""
    if (target and target.startswith("/") and not target.startswith("//")
            and "\\" not in target and all(ord(c) >= 32 for c in target)):
        return target
    return url_for("core.dashboard")


def _fail(message: str, data: dict, status: int):
    if _wants_json():
        return jsonify({"error": message}), status
    return render_template("auth/login.html", errors=[message], form=data,
                           otp_required=False), status


def _reset_fail(token, message):
    if _wants_json():
        return jsonify({"error": message}), 400
    return render_template("auth/reset.html", token=token, errors=[message]), 400
