"""HTTP Basics — learn methods, headers and status codes to retrieve a flag.

Not a vulnerability: a guided exercise in speaking HTTP deliberately. The index
explains the rule and advertises a hint header. The flag endpoint only responds
to the correct method + header combination.

Intended solution:  POST (or PUT) <lab>/flag  — the flag is returned as soon as the
right method is used. A wrong method gets 405 with an Allow header.
"""
from __future__ import annotations

from .base import LabHandler, LabResult

ALLOWED_METHODS = ("POST", "PUT")


class HttpBasicsLab(LabHandler):
    kind = "http_basics"
    title = "HTTP Basics"

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        sub = subpath.strip("/")

        if sub == "flag":
            if request.method not in ALLOWED_METHODS:
                return LabResult(
                    "This endpoint does not answer that HTTP method.\n",
                    status=405, content_type="text/plain; charset=utf-8",
                    headers={"Allow": ", ".join(ALLOWED_METHODS)},
                )
            return LabResult(
                f"Access granted. Flag: {instance['flag']}\n",
                content_type="text/plain; charset=utf-8",
            )

        # Public landing page. Protocol behavior is discoverable from responses.
        body = f"""
<h1>Internal Service</h1>
<div class="card"><p>Service status: online.</p>
<a href="{base}/flag">Restricted endpoint</a>
<p class="muted">Try it from a terminal:</p>
<pre class="laburl-cmd" data-path="{base}/flag"></pre></div>"""
        return LabResult(self.page(instance, "Internal Service", body))
