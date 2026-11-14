"""Stored (persistent) XSS — a comment board whose comments are rendered unescaped.

A comment is stored per-instance and shown to every visitor. A simulated "admin"
reviews comments on a separate endpoint; if a stored comment contains a payload
that would execute and call the benign myctfSolve() proof function (reused from
the reflected-XSS checker), the admin's view "runs" it and reveals the flag —
modelling the victim's browser executing stored script, with no cookie theft.

Intended solution: post a comment like <img src=x onerror=myctfSolve()>, then
trigger the admin review.

Remediation: escape on output, sanitise stored HTML, and set a strict CSP.
"""
from __future__ import annotations

import html

from .base import LabHandler, LabResult, get_state
from .xss import PROOF, payload_executes


class StoredXssLab(LabHandler):
    kind = "stored_xss"
    title = "DevBoard — Comments"

    def _comments(self, instance) -> list:
        st = get_state(instance["id"])
        if "comments" not in st:
            st["comments"] = [
                {"who": "alice", "body": "First! Nice board."},
                {"who": "bob", "body": "Does this support markdown?"},
            ]
        return st["comments"]

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        comments = self._comments(instance)
        sub = subpath.strip("/")

        if request.method == "POST" and sub == "comment":
            body = request.form.get("body", "")
            if body.strip():
                comments.append({"who": "you", "body": body})
            return LabResult("", status=302, headers={"Location": base + "/"})

        if sub == "admin":
            # The "moderator" views every comment. If any would execute, it runs.
            for c in comments:
                rendered = f'<div>{c["body"]}</div>'
                if payload_executes(rendered, c["body"]):
                    return LabResult(self.page(instance, "Moderator", f"""
<h1>Moderator review</h1>
<div class="card"><p class="flag">A stored comment executed in the moderator's
  browser (myctfSolve ran). Flag: {instance['flag']}</p></div>
<p class="muted">Review the comments below.</p>"""))
            return LabResult(self.page(instance, "Moderator", """
<h1>Moderator review</h1>
<div class="card"><p>No active content detected in comments. Looks clean.</p></div>"""))

        # public board (renders comments UNESCAPED — the bug)
        items = "".join(
            f'<div class="card"><b>{html.escape(c["who"])}</b>: {c["body"]}</div>'
            for c in comments
        )
        body = f"""
<h1>DevBoard</h1>
<p class="muted">Leave a comment. A moderator reviews new comments at
   <a href="{base}/admin">{base}/admin</a>.</p>
<div class="card">
  <form method="post" action="{base}/comment">
    <label>Comment</label>
    <textarea name="body" rows="3" placeholder="Say something…"></textarea>
    <button type="submit">Post comment</button>
  </form>
</div>
{items}
<script>
  window.{PROOF} = function(){{ document.title='XSS-OK'; }};
</script>
<p class="muted">Comments are rendered as HTML. The page defines
   <code>{PROOF}()</code>; make a stored comment call it, then trigger the
   moderator review.</p>"""
        return LabResult(self.page(instance, "DevBoard", body))
