"""IDOR — Insecure Direct Object Reference on a simulated banking API.

All accounts and data are synthetic. The learner is issued account 1001. The
account API returns any account by id with NO authorization check (the bug). The
flag lives in the profile of account 1002, which the learner is not meant to see.

Intended solution: call GET <lab>/api/account/1002 (change the id) and read the
``note`` field.

Remediation: enforce object-level authorization — verify the requested object
belongs to the authenticated principal before returning it.
"""
from __future__ import annotations

import json

from .base import LabHandler, LabResult, get_state


class IdorBankLab(LabHandler):
    kind = "idor_bank"
    title = "NimbusBank — Account Portal"

    def _accounts(self, instance) -> dict:
        st = get_state(instance["id"])
        acc = st.get("accounts")
        if acc is None:
            acc = {
                "1001": {"id": "1001", "owner": "you@training.local",
                         "name": "Your Training Account", "balance": 4210.55,
                         "note": "Welcome. Your account id is 1001."},
                "1002": {"id": "1002", "owner": "treasury@nimbusbank.local",
                         "name": "Corporate Treasury", "balance": 918342.00,
                         "note": f"CONFIDENTIAL reconciliation token: {instance['flag']}"},
                "1003": {"id": "1003", "owner": "p.nkemdirim@nimbusbank.local",
                         "name": "Priya N.", "balance": 220.10,
                         "note": "Vacation hold until next month."},
            }
            st["accounts"] = acc
        return acc

    def provision(self, instance) -> None:
        self._accounts(instance)

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        accounts = self._accounts(instance)
        base = self.base_url(instance)

        if subpath.startswith("api/account/"):
            acc_id = subpath.split("/", 2)[2].strip("/")
            # --- VULNERABLE: no check that acc_id == session account ---------
            acc = accounts.get(acc_id)
            if acc is None:
                return LabResult(json.dumps({"error": "not found"}), status=404,
                                 content_type="application/json")
            return LabResult(json.dumps(acc), content_type="application/json")

        # default: the portal page the learner "logs into" as 1001
        me = accounts["1001"]
        body = f"""
<h1>NimbusBank Portal</h1>
<p class="muted">Signed in as <b>{me['owner']}</b> — account #{me['id']}.</p>
<div class="card">
  <h2>Account summary</h2>
  <table>
    <tr><th>Account</th><td>#{me['id']}</td></tr>
    <tr><th>Name</th><td>{me['name']}</td></tr>
    <tr><th>Balance</th><td>${me['balance']:,.2f}</td></tr>
    <tr><th>Note</th><td>{me['note']}</td></tr>
  </table>
  <p class="muted">Your details are loaded from
     <code>GET {base}/api/account/{me['id']}</code>.</p>
</div>
<div class="card">
  <h2>Try the API</h2>
  <p class="muted">The portal fetches account data by id. What happens if you
     request a different id?</p>
  <pre>curl {base}/api/account/1001</pre>
</div>"""
        return LabResult(self.page(instance, "NimbusBank", body))
