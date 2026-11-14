"""Insecure File Upload — missing server-side file-type validation.

The profile-picture uploader claims to accept images, but performs NO real
server-side validation: it stores whatever is sent and would serve it back as
executable content. Uploading a server-side script (e.g. shell.php) is accepted
and — in this safe simulation — "executed", revealing the flag. No real file is
written and no code runs; the handler just recognises that a dangerous upload was
permitted.

Intended solution: upload a file named like shell.php (any non-image executable
extension).

Remediation: validate on the server by content (magic bytes), enforce an
allow-list of safe extensions, store outside the web root, randomise names, and
never serve uploads as executable.
"""
from __future__ import annotations

import html
import posixpath

from .base import LabHandler, LabResult

IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "bmp"}
DANGEROUS_EXTS = {"php", "phtml", "php5", "jsp", "asp", "aspx", "svg", "html",
                  "htm", "js", "sh", "py", "cgi"}


class FileUploadLab(LabHandler):
    kind = "file_upload"
    title = "ProfilePix — Avatar Upload"

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        sub = subpath.strip("/")
        result = ""

        if request.method == "POST" and sub == "upload":
            f = next(iter(request.files.values()), None)
            if f is None or not f.filename:
                result = '<p class="err">No file selected.</p>'
            else:
                name = posixpath.basename(f.filename)
                ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                # --- VULNERABLE: no real validation; dangerous types accepted --
                if ext in DANGEROUS_EXTS:
                    result = (f'<p class="flag">Uploaded <code>{html.escape(name)}</code> '
                              f'to /uploads/ and served it as executable — the server '
                              f'would run this. Flag: {instance["flag"]}</p>')
                elif ext in IMAGE_EXTS:
                    result = (f'<p>Uploaded <code>{html.escape(name)}</code>. '
                              f'Looks like an image — nothing interesting happens.</p>')
                else:
                    result = (f'<p>Uploaded <code>{html.escape(name)}</code> '
                              f'({ext or "no extension"}). Stored, but not executed.</p>')

        banner = f'<div class="card">{result}</div>' if result else ""
        body = f"""
<h1>ProfilePix</h1>
<p class="muted">Upload a profile picture. <b>Images only</b> (the UI says so).</p>
{banner}
<div class="card">
  <form method="post" action="{base}/upload" enctype="multipart/form-data">
    <label>Avatar file</label>
    <input type="file" name="avatar">
    <button type="submit">Upload</button>
  </form>
</div>
<p class="muted">The server trusts the file you send. What if it isn't an image —
   say a <code>.php</code> script?</p>"""
        return LabResult(self.page(instance, "ProfilePix", body))
