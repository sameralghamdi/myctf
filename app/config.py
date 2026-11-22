"""Application configuration.

Secrets come from the environment. In this dev build we fall back to a
generated per-process secret so the app runs out of the box, but production
MUST set MYCTF_SECRET_KEY (see docs/ARCHITECTURE.md).
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
CHALLENGE_DIR = BASE_DIR / "challenges"


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # --- security ---
    SECRET_KEY = os.environ.get("MYCTF_SECRET_KEY") or secrets.token_hex(32)
    # Token lifetime for an authenticated session (seconds).
    SESSION_TTL = int(os.environ.get("MYCTF_SESSION_TTL", str(60 * 60 * 12)))
    # PBKDF2 iterations for password hashing.
    PBKDF2_ITERATIONS = int(os.environ.get("MYCTF_PBKDF2_ITERS", "600000"))

    # --- database ---
    DB_PATH = os.environ.get("MYCTF_DB_PATH", str(INSTANCE_DIR / "myctf.sqlite3"))
    CHALLENGE_DIR = str(CHALLENGE_DIR)

    # --- labs ---
    # How long a lab instance lives before it is auto-expired (seconds).
    LAB_TTL = int(os.environ.get("MYCTF_LAB_TTL", str(60 * 45)))
    # Max simultaneous running labs per user (resource guard).
    LAB_MAX_PER_USER = int(os.environ.get("MYCTF_LAB_MAX_PER_USER", "6"))

    # --- scoring ---
    DIFFICULTY_POINTS = {
        "very_easy": 50,
        "easy": 100,
        "medium": 200,
        "hard": 350,
        "insane": 500,
    }

    # --- rate limiting (simple in-process limiter; Redis in production) ---
    RATE_LIMIT_WINDOW = int(os.environ.get("MYCTF_RL_WINDOW", "60"))
    RATE_LIMIT_FLAG_SUBMITS = int(os.environ.get("MYCTF_RL_FLAG", "20"))
    RATE_LIMIT_LOGIN = int(os.environ.get("MYCTF_RL_LOGIN", "10"))

    # --- bootstrap admin, created on first start if it does not exist ---
    # There is NO default password. If MYCTF_ADMIN_PASSWORD is unset, a random
    # one is generated and printed once in the server log (see seed.py).
    SEED_ADMIN_USER = os.environ.get("MYCTF_ADMIN_USER", "admin")
    SEED_ADMIN_EMAIL = os.environ.get("MYCTF_ADMIN_EMAIL", "admin@myctf.local")
    SEED_ADMIN_PASSWORD = os.environ.get("MYCTF_ADMIN_PASSWORD") or None

    # --- deployment (see docs/DEPLOYMENT.md) ---
    # Set MYCTF_COOKIE_SECURE=1 whenever the site is served over HTTPS.
    COOKIE_SECURE = _env_bool("MYCTF_COOKIE_SECURE", False)
    # There is no mailer yet. When on, the API returns reset/verify links in the
    # response body so the flow can be tried locally. NEVER enable on a public site.
    EXPOSE_DEV_LINKS = _env_bool("MYCTF_EXPOSE_DEV_LINKS", False)
    # Behind Cloudflare / a reverse proxy: trust X-Forwarded-* for client IPs.
    TRUST_PROXY = _env_bool("MYCTF_TRUST_PROXY", False)
    # Shared secret the Cloudflare Pages proxy sends as X-Origin-Secret. When set,
    # requests without it are rejected, so the API can't be hit directly.
    ORIGIN_SECRET = os.environ.get("MYCTF_ORIGIN_SECRET", "")
    # Browser origins allowed to make state-changing requests (CSRF guard), e.g.
    # "https://ctf.example.com". Empty = same-origin only (fine for local dev).
    ALLOWED_ORIGINS = [o.strip().rstrip("/").lower() for o in
                       os.environ.get("MYCTF_ALLOWED_ORIGINS", "").split(",") if o.strip()]
    # Reject request bodies larger than this (bytes).
    MAX_CONTENT_LENGTH = int(os.environ.get("MYCTF_MAX_BODY", str(1024 * 1024)))
    RATE_LIMIT_REGISTER = int(os.environ.get("MYCTF_RL_REGISTER", "20"))   # per hour / IP
    RATE_LIMIT_RESET = int(os.environ.get("MYCTF_RL_RESET", "5"))          # per 15 min / IP
    # Ceiling for ALL requests from one IP per minute (0 = off). Generous on
    # purpose: a whole classroom can share one address.
    RATE_LIMIT_GLOBAL = int(os.environ.get("MYCTF_RL_GLOBAL", "1200"))

    # --- email (sign-in codes, password reset) ---
    # Without MYCTF_SMTP_HOST, emails are printed to the server log (dev) instead.
    SMTP_HOST = os.environ.get("MYCTF_SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("MYCTF_SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("MYCTF_SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("MYCTF_SMTP_PASSWORD", "")
    # "starttls" (port 587), "ssl" (port 465) or "none".
    SMTP_SECURITY = os.environ.get("MYCTF_SMTP_SECURITY", "starttls").strip().lower()
    MAIL_FROM = os.environ.get("MYCTF_MAIL_FROM", "MyCTF <no-reply@localhost>")
    # Where links in emails point, e.g. https://myctf.app (defaults to the first allowed origin).
    PUBLIC_URL = os.environ.get("MYCTF_PUBLIC_URL", "")
    # Email a 6-digit code at every sign-in: "auto" = on when SMTP is configured, "1" = always, "0" = off.
    LOGIN_EMAIL_OTP = os.environ.get("MYCTF_LOGIN_EMAIL_OTP", "auto").strip().lower()
    LOGIN_CODE_TTL = 10 * 60

    TESTING = False


class TestConfig(Config):
    TESTING = True
    SEED_ADMIN_PASSWORD = "ChangeMe_Admin!123"   # test fixture only
    EXPOSE_DEV_LINKS = True
    PBKDF2_ITERATIONS = 10_000  # keep tests fast; never use in production
    DB_PATH = ":memory:"
    LAB_TTL = 60 * 10
