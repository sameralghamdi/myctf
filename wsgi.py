"""Production entrypoint:  gunicorn wsgi:app

Refuses to start in production with the dev defaults, because the default
admin password and a per-process random secret key are both unsafe on a public
server.
"""
from __future__ import annotations

import os
import threading

# Passwords that appeared in old docs/examples: never acceptable in production.
_KNOWN_WEAK = {"ChangeMe_Admin!123", "CHANGE_ME", "admin", "password"}

if os.environ.get("MYCTF_ENV") == "production":
    problems = []
    secret = os.environ.get("MYCTF_SECRET_KEY", "")
    if len(secret) < 32 or "change" in secret.lower():
        problems.append("MYCTF_SECRET_KEY must be set to a random value of 32+ characters")
    admin_pw = os.environ.get("MYCTF_ADMIN_PASSWORD", "")
    if admin_pw in _KNOWN_WEAK or len(admin_pw) < 12:
        problems.append("MYCTF_ADMIN_PASSWORD must be changed (12+ characters)")
    if os.environ.get("MYCTF_EXPOSE_DEV_LINKS", "").lower() in {"1", "true", "yes", "on"}:
        problems.append("MYCTF_EXPOSE_DEV_LINKS must be off on a public site")
    if not os.environ.get("MYCTF_ORIGIN_SECRET"):
        problems.append("MYCTF_ORIGIN_SECRET must be set (shared with the Cloudflare proxy)")
    if os.environ.get("MYCTF_COOKIE_SECURE", "").lower() not in {"1", "true", "yes", "on"}:
        problems.append("MYCTF_COOKIE_SECURE=1 is required (the site is served over HTTPS)")
    if not os.environ.get("MYCTF_ALLOWED_ORIGINS"):
        problems.append("MYCTF_ALLOWED_ORIGINS must list your site, e.g. https://ctf.example.com")
    if os.environ.get("MYCTF_DEBUG"):
        problems.append("MYCTF_DEBUG must be unset")
    if problems:
        raise SystemExit("Refusing to start:\n - " + "\n - ".join(problems))

from run import _lab_sweeper, app  # noqa: E402  (imports create_app after the checks)

if os.environ.get("MYCTF_SWEEPER", "1") == "1":
    threading.Thread(target=_lab_sweeper, args=(app,), daemon=True).start()
