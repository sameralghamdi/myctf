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

        # index
        body = f"""
<h1>HTTP Basics</h1>
<div class="card">
  <p>HTTP requests carry a <b>method</b> (GET, POST, …) and <b>headers</b>.
     The flag endpoint is picky about both.</p>
  <ol>
    <li>The flag lives at <code>{base}/flag</code>.</li>
    <li>It only answers the <code>POST</code> method.</li>
    <li>It requires the header
        <code>{REQUIRED_HEADER}: {REQUIRED_VALUE}</code>.</li>
  </ol>
  <p class="muted">Watch the response headers too — a <code>X-Hint</code> header
     is returned when you get it wrong.</p>
  <pre>curl -X POST {{origin}}{base}/flag \\
     -H '{REQUIRED_HEADER}: {REQUIRED_VALUE}'</pre>
</div>"""
        return LabResult(self.page(instance, "HTTP Basics", body),
                         headers={"X-Hint": f"POST {base}/flag with {REQUIRED_HEADER}"})
