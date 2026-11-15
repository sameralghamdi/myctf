"""Reflected XSS — search box that echoes input unescaped (training target).

Proof-of-execution is HARMLESS: the learner must craft a payload that would call
the benign ``myctfSolve()`` function the page defines. No cookie theft, no
exfiltration — the spec's "harmless proof of execution" rule. A server-side
checker recognises a payload that *would* execute (breaks out of the HTML context
and invokes myctfSolve) and reveals the per-instance flag when it does.

Intended solutions include:
    <script>myctfSolve()</script>
    <img src=x onerror=myctfSolve()>

Remediation: contextually escape output (HTML-encode), prefer frameworks that
auto-escape, and apply a Content-Security-Policy that blocks inline script.
"""
from __future__ import annotations

import re

from .base import LabHandler, LabResult

PROOF = "myctfSolve"


def payload_executes(reflected_html: str, payload: str) -> bool:
    """True if `payload` survived unescaped AND forms an executing call to PROOF.

    This is the automated-checker stand-in for a browser actually running the
    script. It intentionally accepts the canonical XSS shapes.
    """
    if not payload or payload not in reflected_html:
        return False  # output was escaped/encoded -> not exploitable
    low = payload.lower()
    proof = PROOF.lower()
    if proof not in low:
        return False
    patterns = [
        r"<script[^>]*>[^<]*" + proof,                 # <script>myctfSolve()</script>
        r"<[a-z][a-z0-9]*\b[^>]*\son[a-z]+\s*=\s*[^>]*" + proof,  # onerror=/onload=
        r"javascript:[^\"'>]*" + proof,                # javascript: URI
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
        return LabResult(self.page(instance, "SearchHub", body))
