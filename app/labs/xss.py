"""Reflected XSS — search box that echoes input unescaped (training target).

Proof-of-execution is HARMLESS: the learner must craft a payload that would call
the benign ``myctfSolve()`` function the page defines. No cookie theft, no
exfiltration — the spec's "harmless proof of execution" rule. A server-side
checker recognises a payload that *would* execute (breaks out of the HTML context
and invokes myctfSolve) and reveals the per-instance flag when it does.

Any payload that would execute script reveals the flag, e.g.:
    <script>alert(1)</script>
    <img src=x onerror=alert(1)>

Remediation: contextually escape output (HTML-encode), prefer frameworks that
auto-escape, and apply a Content-Security-Policy that blocks inline script.
"""
from __future__ import annotations

import re

from .base import LabHandler, LabResult

PROOF = "myctfSolve"


def payload_executes(reflected_html: str, payload: str) -> bool:
    """True if `payload` survived unescaped AND is a script-executing shape.

    Stand-in for a browser actually running the script. ANY working XSS payload
    counts (it does not have to call myctfSolve): a <script> element, an inline
    event handler on a tag, or a javascript: URI.
    """
    if not payload or payload not in reflected_html:
        return False  # output was escaped/encoded -> not exploitable
    low = payload.lower()
    patterns = [
        r"<script\b",                                   # <script>...</script>
        r"<[a-z][a-z0-9]*\b[^>]*\son[a-z]+\s*=",       # onerror= / onload= / ...
        r"javascript:",                                  # javascript: URI
    ]
    return any(re.search(p, low) for p in patterns)


class ReflectedXssLab(LabHandler):
    kind = "reflected_xss"
    title = "SearchHub — Reflected Search"

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        q = request.args.get("q", "")

        # --- VULNERABLE: q echoed into the page without escaping -------------
        reflected = f'<div class="card">You searched for: {q}</div>' if q else ""

        solved_block = ""
        if q and payload_executes(reflected, q):
            solved_block = (
                f'<div class="card"><p class="flag">myctfSolve() executed — '
                f'flag: {instance["flag"]}</p></div>'
            )

        body = f"""
<h1>SearchHub</h1>
<p class="muted">Search our catalogue. Your query is shown back to you below.</p>
<div class="card">
  <form method="get" action="{base}/">
    <label>Search</label>
    <input name="q" value="" autofocus placeholder="laptops">
    <button type="submit">Search</button>
  </form>
</div>
{reflected}
{solved_block}
<script>
  // Benign proof-of-execution hook. A successful XSS calls this.
  window.{PROOF} = function(){{
     document.title = 'XSS-OK';
     var d = document.createElement('div');
     d.className='card'; d.innerHTML='<p class="flag">myctfSolve() ran in your browser.</p>';
     document.body.appendChild(d);
  }};
</script>
"""
        # SAFETY: the payload really executes in the learner's browser, so the
        # page is served in a CSP sandbox (no allow-same-origin): scripts run, but
        # in an opaque origin with no access to the MyCTF session or API.
        return LabResult(self.page(instance, "SearchHub", body), headers={
            "Content-Security-Policy": "sandbox allow-scripts allow-modals allow-forms; frame-ancestors 'self'",
        })
