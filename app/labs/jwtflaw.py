"""JWT Authorization Flaw — the classic 'alg: none' acceptance bug.

The lab issues a signed (HS256) session JWT for a low-privileged 'guest'. The
admin endpoint decodes the token with a flawed verifier that TRUSTS the token's
own 'alg' header: if it says 'none', the signature is not checked. An attacker
re-encodes the token with alg=none and role=admin to forge an admin session.

Intended solution: build  header {"alg":"none"} . payload {"role":"admin"} .  (empty
signature) and present it to the admin endpoint.

Remediation: pin the accepted algorithm server-side, never honour the token's own
alg, reject 'none', and verify signatures with a vetted library.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json

from .base import LabHandler, LabResult


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64u_dec(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s.encode())


class JwtFlawLab(LabHandler):
    kind = "jwt_flaw"
    title = "SecureApp — JWT Session"

    SECRET = "lab-signing-key-not-the-point"

    def _guest_token(self) -> str:
        header = _b64u(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        payload = _b64u(json.dumps({"user": "guest", "role": "user"}).encode())
        signing = f"{header}.{payload}".encode()
        sig = _b64u(hmac.new(self.SECRET.encode(), signing, hashlib.sha256).digest())
        return f"{header}.{payload}.{sig}"

    def _verify(self, token: str):
        # --- VULNERABLE: trusts the token's own alg header -----------------
        try:
            h, p, s = token.split(".")
            header = json.loads(_b64u_dec(h))
            payload = json.loads(_b64u_dec(p))
        except Exception:
            return None
        alg = header.get("alg", "")
        if alg == "none":
            return payload                       # <-- signature NOT verified
        if alg == "HS256":
            expected = _b64u(hmac.new(self.SECRET.encode(),
                                      f"{h}.{p}".encode(), hashlib.sha256).digest())
            if hmac.compare_digest(expected, s):
                return payload
            return None
        return None

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        sub = subpath.strip("/")

        if sub == "admin":
            # An explicit ?token= wins; otherwise fall back to a Bearer header.
            token = request.args.get("token")
            if not token:
                auth = request.headers.get("Authorization", "")
                token = auth[7:].strip() if auth.startswith("Bearer ") else ""
            payload = self._verify(token)
            if payload and payload.get("role") == "admin":
                return LabResult(self.page(instance, "Admin", f"""
<h1>Admin console</h1>
<div class="card"><p class="flag">Welcome, admin. Flag: {instance['flag']}</p></div>"""))
            role = (payload or {}).get("role", "anonymous")
            return LabResult(self.page(instance, "Admin", f"""
<h1>Admin console</h1>
<div class="card"><p class="err">Access denied for role: {role}. Admins only.</p></div>
<p class="muted">Present an admin token via <code>?token=</code> or an
   <code>Authorization: Bearer</code> header.</p>"""), status=403)

        token = self._guest_token()
        body = f"""
<h1>SecureApp</h1>
<p class="muted">You are signed in as <b>guest</b>. Your session JWT:</p>
<div class="card"><pre style="white-space:pre-wrap;word-break:break-all">{token}</pre></div>
<div class="card">
  <h2>Admin area</h2>
  <p class="muted">Restricted account area: <a href="{base}/admin">Administrator console</a></p>
  <pre>curl "{{origin}}{base}/admin?token=&lt;your-token&gt;"</pre>
</div>
"""
        return LabResult(self.page(instance, "SecureApp", body))
