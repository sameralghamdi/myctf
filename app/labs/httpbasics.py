"""HTTP Basics — learn methods, headers and status codes to retrieve a flag.

Not a vulnerability: a guided exercise in speaking HTTP deliberately. The index
explains the rule and advertises a hint header. The flag endpoint only responds
to the correct method + header combination.

Intended solution:  POST <lab>/flag  with header  X-MyCTF-Access: let-me-in
"""
from __future__ import annotations

from .base import LabHandler, LabResult

REQUIRED_HEADER = "X-MyCTF-Access"
REQUIRED_VALUE = "let-me-in"


class HttpBasicsLab(LabHandler):
    kind = "http_basics"
    title = "HTTP Basics"

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        sub = subpath.strip("/")

        if sub == "flag":
            if request.method != "POST":
                return LabResult(
                    "This endpoint only answers POST requests.\n",
                    status=405, content_type="text/plain; charset=utf-8",
                    headers={"Allow": "POST",
                             "X-Hint": f"send header {REQUIRED_HEADER}: {REQUIRED_VALUE}"},
                )
            if request.headers.get(REQUIRED_HEADER) != REQUIRED_VALUE:
                return LabResult(
                    "Missing or wrong access header.\n",
                    status=403, content_type="text/plain; charset=utf-8",
                    headers={"X-Hint": f"header {REQUIRED_HEADER} must be '{REQUIRED_VALUE}'"},
                )
            return LabResult(
                f"Access granted. Flag: {instance['flag']}\n",
                content_type="text/plain; charset=utf-8",
            )

        # Public landing page. Protocol behavior is discoverable from responses.
        body = f"""
<h1>Internal Service</h1>
<div class="card"><p>Service status: online.</p>
<a href="{base}/flag">Restricted endpoint</a></div>"""
        return LabResult(self.page(instance, "Internal Service", body))
