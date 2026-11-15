"""Path Traversal — document viewer over a SAFE virtual filesystem.

No real filesystem is touched. The "files" are a dict of virtual paths. The
viewer joins a fixed base dir with user input and normalises it — exactly the
real-world bug — but resolution happens against the in-memory dict, so traversal
is demonstrable while being completely harmless to the host.

Intended base dir: ``docs/``. The flag file lives at ``secret/flag.txt``, outside
``docs``. Intended solution: ``?file=../secret/flag.txt``.

Remediation: resolve the canonical path and verify it stays within the intended
directory (e.g. os.path.realpath + prefix check), or map to an allow-list of ids.
"""
from __future__ import annotations

import html
import posixpath

from .base import LabHandler, LabResult


class PathTraversalLab(LabHandler):
    kind = "path_traversal"
    title = "DocuView — Internal Document Viewer"

    BASE = "docs"

    def _vfs(self, instance) -> dict:
        return {
            "docs/welcome.txt": "Welcome to DocuView. Pick a document to read.",
            "docs/handbook.txt": "Employee handbook: be excellent to each other.",
            "docs/changelog.txt": "v1.2 - added the document viewer.",
            "secret/flag.txt": instance["flag"],
            "secret/admin_notes.txt": "Rotate the viewer credentials quarterly.",
        }

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        vfs = self._vfs(instance)
        requested = request.args.get("file")

        listing = "".join(
            f'<li><a href="{base}/?file={p.split("/",1)[1]}">'
            f'{html.escape(p.split("/",1)[1])}</a></li>'
            for p in vfs if p.startswith("docs/")
        )

        content_block = ""
        if requested is not None:
            # --- VULNERABLE: naive join + normalise, no containment check ----
            joined = posixpath.normpath(posixpath.join(self.BASE, requested))
            data = vfs.get(joined)
            if data is None:
                content_block = (f'<div class="card"><p class="err">'
                                 f'Not found: {html.escape(joined)}</p></div>')
            else:
                content_block = (
                    f'<div class="card"><h2>{html.escape(joined)}</h2>'
                    f'<pre>{html.escape(data)}</pre></div>'
                )

        body = f"""
<h1>DocuView</h1>
<p class="muted">Internal document viewer. Base directory:
   <code>{self.BASE}/</code></p>
<div class="card"><h2>Available documents</h2><ul>{listing}</ul></div>
{content_block}
"""
        return LabResult(self.page(instance, "DocuView", body))
