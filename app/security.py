"""Security primitives: password hashing, auth tokens, flags, constant-time checks.

Dependency-light on purpose (this sandbox cannot install passlib/argon2). We use
PBKDF2-HMAC-SHA256 from the stdlib, which is a sound, FIPS-approved KDF. The
production notes in docs/ARCHITECTURE.md describe moving to Argon2id.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time

import jwt  # PyJWT

# --- password hashing --------------------------------------------------------
# Stored format:  pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>


def hash_password(password: str, *, iterations: int = 600_000) -> str:
    if not password:
        raise ValueError("empty password")
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters_s, salt_b64, hash_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, TypeError):
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(dk, expected)


# --- flag hashing / comparison ----------------------------------------------
# Static flags are stored hashed. Comparison is always constant-time.


def hash_flag(flag: str, secret: str) -> str:
    return hmac.new(secret.encode(), flag.strip().encode(), hashlib.sha256).hexdigest()


def flags_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a.strip().encode(), b.strip().encode())


def flag_matches_hash(submitted: str, stored_hash: str, secret: str) -> bool:
    return hmac.compare_digest(hash_flag(submitted, secret), stored_hash or "")


# --- auth tokens (JWT over server-side session rows) -------------------------


def issue_token(*, user_id: int, session_id: str, secret: str, ttl: int) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "jti": session_id,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict | None:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


# --- misc --------------------------------------------------------------------


def new_id(nbytes: int = 16) -> str:
    return secrets.token_hex(nbytes)


def random_flag(label: str = "") -> str:
    """Per-session flag. Without a label (the default for labs): MYCTF{9f2c41...}."""
    token = secrets.token_hex(12)
    return "MYCTF{%s_%s}" % (label, token) if label else "MYCTF{%s}" % token


def hash_token(raw: str, secret: str) -> str:
    return hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()


# --- TOTP (RFC 6238) — stdlib implementation (no pyotp dependency) -----------
def new_totp_secret() -> str:
    """Return a base32 secret suitable for authenticator apps."""
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _hotp(secret_b32: str, counter: int, digits: int = 6) -> str:
    pad = "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(secret_b32.upper() + pad)
    msg = counter.to_bytes(8, "big")
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = ((digest[offset] & 0x7F) << 24 | (digest[offset + 1] & 0xFF) << 16 |
            (digest[offset + 2] & 0xFF) << 8 | (digest[offset + 3] & 0xFF))
    return str(code % (10 ** digits)).zfill(digits)


def totp_now(secret_b32: str, step: int = 30) -> str:
    return _hotp(secret_b32, int(time.time()) // step)


def totp_verify(secret_b32: str, code: str, step: int = 30, window: int = 1) -> bool:
    if not code or not code.isdigit():
        return False
    counter = int(time.time()) // step
    for drift in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret_b32, counter + drift), code):
            return True
    return False


def totp_uri(secret_b32: str, account: str, issuer: str = "MyCTF") -> str:
    from urllib.parse import quote
    label = quote(f"{issuer}:{account}")
    return (f"otpauth://totp/{label}?secret={secret_b32}"
            f"&issuer={quote(issuer)}&digits=6&period=30")
