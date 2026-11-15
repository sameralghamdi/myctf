"""Authentication helpers: current user resolution and access decorators.

Auth is a JWT (HS256) whose ``jti`` references a server-side ``sessions`` row, so
tokens are revocable (logout / expiry). The token is delivered as an HttpOnly
cookie for the browser UI and also accepted as ``Authorization: Bearer`` for API
clients and tests.
"""
from __future__ import annotations

import functools

from flask import current_app, g, request

from .. import models
from ..security import decode_token

COOKIE_NAME = "myctf_token"
ROLE_RANK = {"student": 1, "instructor": 2, "administrator": 3}


def _extract_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return request.cookies.get(COOKIE_NAME)


def current_user():
    """Resolve the authenticated user for this request, or None. Cached on g."""
    if "current_user" in g:
        return g.current_user
    user = None
    token = _extract_token()
    if token:
        payload = decode_token(token, current_app.config["SECRET_KEY"])
        if payload and models.session_is_active(payload.get("jti", "")):
            user = models.get_user_by_id(int(payload["sub"]))
    g.current_user = user
    return user


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return _deny(401, "Authentication required.")
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def deco(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return _deny(401, "Authentication required.")
            if user["role"] not in roles:
                return _deny(403, "Insufficient role.")
            return view(*args, **kwargs)
        return wrapped
    return deco


def admin_required(view):
    return role_required("administrator")(view)


def _deny(status: int, message: str):
    from flask import jsonify, redirect, url_for
    # API callers get JSON; browsers get redirected to login on 401.
    wants_json = (request.path.startswith(("/api/", "/admin/api/"))
                  or "application/json" in request.headers.get("Accept", ""))
    if wants_json:
        return jsonify({"error": message}), status
    if status == 401:
        return redirect(url_for("auth.login_page", next=request.path))
    from flask import abort
    abort(status, message)
