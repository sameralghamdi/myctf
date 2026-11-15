"""API — Broken Object Level Authorization (BOLA / OWASP API #1).

A documented REST API authenticates the caller with a static API key but never
checks that a requested order belongs to that caller. Any order id can be read.

Intended solution: with the provided key, request an order that isn't yours
(5002) and read its 'notes' field.

Remediation: enforce per-object authorization on every endpoint — the
authenticated principal must own (or be permitted) the object before it's served.
"""
from __future__ import annotations

import json

from .base import LabHandler, LabResult

API_KEY = "sk_live_guest_9f2a"


class BolaApiLab(LabHandler):
    kind = "bola_api"
    title = "ShopAPI — Orders"

    def _orders(self, instance) -> dict:
        return {
            "5001": {"id": "5001", "owner": "guest", "item": "USB-C cable",
                     "total": 12.99, "notes": "Leave at front desk."},
            "5002": {"id": "5002", "owner": "corp-admin", "item": "Server rack",
                     "total": 4820.00,
                     "notes": f"Internal PO approval code: {instance['flag']}"},
            "5003": {"id": "5003", "owner": "mia", "item": "Mechanical keyboard",
                     "total": 89.50, "notes": "Gift wrap."},
        }

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        sub = subpath.strip("/")

        if sub.startswith("api/orders/"):
            key = request.headers.get("X-API-Key") or request.args.get("api_key")
            if key != API_KEY:
                return LabResult(json.dumps({"error": "missing or invalid API key"}),
                                 status=401, content_type="application/json")
            oid = sub.split("/", 2)[2].strip("/")
            # --- VULNERABLE: authenticated, but no per-object authorization ---
            order = self._orders(instance).get(oid)
            if order is None:
                return LabResult(json.dumps({"error": "order not found"}),
                                 status=404, content_type="application/json")
            return LabResult(json.dumps(order), content_type="application/json")

        body = f"""
<h1>ShopAPI</h1>
<p class="muted">REST API for your orders. Authenticate with the API key below.</p>
<div class="card">
  <h2>Credentials</h2>
  <p>Your API key: <code>{API_KEY}</code> · your user: <b>guest</b> (order 5001)</p>
</div>
<div class="card">
  <h2>Endpoint</h2>
  <pre>GET {base}/api/orders/&lt;id&gt;
Header:  X-API-Key: {API_KEY}</pre>
  <p class="muted">Try your own order first:</p>
  <pre>curl -H "X-API-Key: {API_KEY}" "{{origin}}{base}/api/orders/5001"</pre>
</div>
"""
        return LabResult(self.page(instance, "ShopAPI", body))
