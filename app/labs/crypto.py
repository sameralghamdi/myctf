"""Encoding & Decoding — recover a flag hidden under layers of encoding.

Teaches that encoding is not encryption. The per-instance flag is wrapped in two
reversible layers: ROT13 over the inner text, then Base64. The lab shows the
encoded blob and an interactive multi-tool decoder (client-side convenience). The
learner decodes the blob to recover the flag and submits it to the platform.

Intended solution: Base64-decode the blob, then ROT13 the result.
"""
from __future__ import annotations

import base64
import codecs

from .base import LabHandler, LabResult


def encode_challenge(flag: str) -> str:
    rot = codecs.encode(flag, "rot_13")
    return base64.b64encode(rot.encode()).decode()


class EncodingLab(LabHandler):
    kind = "encoding"
    title = "Layered Encoding"

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        blob = encode_challenge(instance["flag"])
        body = f"""
<h1>Encoding &amp; Decoding</h1>
<p class="muted">Encoding is reversible and provides no secrecy. This blob hides a
   flag under two common layers.</p>
<div class="card">
  <h2>Encoded blob</h2>
  <pre id="blob">{blob}</pre>
  <p class="muted">Two layers were applied: an outer transport encoding, then a
     classic letter rotation on the inside.</p>
</div>
<div class="card">
  <h2>Decoder bench</h2>
  <label>Input</label>
  <textarea id="in" rows="3">{blob}</textarea>
  <div>
    <button class="ghost" onclick="op('b64d')">Base64 decode</button>
    <button class="ghost" onclick="op('hexd')">Hex decode</button>
    <button class="ghost" onclick="op('rot13')">ROT13</button>
    <button class="ghost" onclick="op('url')">URL decode</button>
  </div>
  <label>Output</label>
  <textarea id="out" rows="3" readonly></textarea>
  <button class="ghost" onclick="document.getElementById('in').value=
      document.getElementById('out').value">Use output as input ▲</button>
</div>
<script>
 function rot13(s){{return s.replace(/[a-z]/gi,c=>String.fromCharCode(
   (c<='Z'?90:122)>=(c=c.charCodeAt(0)+13)?c:c-26));}}
 function op(k){{
   var v=document.getElementById('in').value, o='';
   try{{
     if(k==='b64d') o=decodeURIComponent(escape(atob(v.trim())));
     else if(k==='hexd') o=v.trim().replace(/\\s+/g,'').replace(/../g,
        h=>String.fromCharCode(parseInt(h,16)));
     else if(k==='rot13') o=rot13(v);
     else if(k==='url') o=decodeURIComponent(v);
   }}catch(e){{o='[error: '+e.message+']';}}
   document.getElementById('out').value=o;
 }}
</script>
<p class="muted">Recover the <code>MYCTF{{...}}</code> flag and submit it on the
   challenge page.</p>"""
        return LabResult(self.page(instance, "Encoding", body))
