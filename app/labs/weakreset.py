"""Weak Password Reset — predictable (sequential) reset tokens.

The app issues password-reset tokens as sequential integers. An attacker who can
request a reset for their own account observes the current token value, then
predicts the token issued for the victim's reset and takes over the account.

Intended solution:
  1. POST /forgot  user=guest      -> you are shown your token (e.g. 1007)
  2. POST /forgot  user=victim     -> victim's token is the next integer (hidden)
  3. POST /reset   user=victim token=<predicted> new_password=...  -> flag

Remediation: use long, random, single-use, expiring tokens (CSPRNG), bound to the
account and never sequential or guessable.
"""
from __future__ import annotations

import html

from .base import LabHandler, LabResult, get_state


class WeakResetLab(LabHandler):
    kind = "weak_reset"
    title = "AccountCenter — Password Reset"

    def _st(self, instance):
        st = get_state(instance["id"])
        if "counter" not in st:
            st["counter"] = 1006
            st["tokens"] = {}          # user -> issued token
        return st

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        st = self._st(instance)
        sub = subpath.strip("/")
        msg = ""

        if request.method == "POST" and sub == "forgot":
            user = (request.form.get("user") or "").strip()
            st["counter"] += 1
            st["tokens"][user] = st["counter"]
            if user == "guest":
                msg = (f'<p class="flag">Reset requested for <b>guest</b>. '
                       f'Your reset token: {st["counter"]}</p>')
            else:
                msg = (f'<p>If <b>{html.escape(user)}</b> exists, a reset link was '
                       f'emailed to them. (token hidden)</p>')

        elif request.method == "POST" and sub == "reset":
            user = (request.form.get("user") or "").strip()
            token = (request.form.get("token") or "").strip()
            issued = st["tokens"].get(user)
            if issued is not None and token.isdigit() and int(token) == issued:
                if user == "victim":
                    msg = (f'<p class="flag">Password for <b>victim</b> reset '
                           f'successfully. Recovery note reveals: {instance["flag"]}</p>')
                else:
                    msg = f'<p>Password for {html.escape(user)} reset.</p>'
            else:
                msg = '<p class="err">Invalid or expired reset token.</p>'

        banner = f'<div class="card">{msg}</div>' if msg else ""
        body = f"""
<h1>AccountCenter</h1>
<p class="muted">Self-service password reset. You have access to the
   <b>guest</b> account; the target account is <b>victim</b>.</p>
{banner}
<div class="card">
  <h2>1 · Request a reset</h2>
  <form method="post" action="{base}/forgot">
    <label>Username</label>
    <input name="user" value="guest">
    <button type="submit">Send reset token</button>
  </form>
</div>
<div class="card">
  <h2>2 · Use a reset token</h2>
  <form method="post" action="{base}/reset">
    <label>Username</label><input name="user" value="victim">
    <label>Reset token</label><input name="token" placeholder="e.g. 1008">
    <label>New password</label><input name="new_password" value="pwned123!">
    <button type="submit">Reset password</button>
  </form>
</div>
<p class="muted">Tokens are issued sequentially. Observe yours, then predict the
   victim's.</p>"""
        return LabResult(self.page(instance, "AccountCenter", body))
