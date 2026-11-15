"""PCAP Investigation (forensics) — find a flag hidden in captured traffic.

A simulated packet capture is rendered like a minimal protocol analyser. One HTTP
POST carries a credential field whose value is the Base64-encoded flag among
decoy packets. The learner inspects payloads, spots the encoded value, and
decodes it.

Intended solution: find the POST to /api/sync, Base64-decode the `recovery`
field.
"""
from __future__ import annotations

import base64
import html

from .base import LabHandler, LabResult


class PcapLab(LabHandler):
    kind = "pcap"
    title = "NetCapture — Traffic Analyser"

    def _packets(self, instance) -> list:
        enc = base64.b64encode(instance["flag"].encode()).decode()
        return [
            ("1", "0.000", "10.0.0.5", "8.8.8.8", "DNS",
             "Standard query A  updates.example.com"),
            ("2", "0.004", "10.0.0.5", "93.184.216.34", "TCP",
             "49512 → 80 [SYN] Seq=0 Win=64240"),
            ("3", "0.021", "10.0.0.5", "93.184.216.34", "HTTP",
             "GET /index.html HTTP/1.1  Host: example.com"),
            ("4", "0.052", "10.0.0.5", "93.184.216.34", "HTTP",
             'POST /api/sync HTTP/1.1  Content-Type: application/x-www-form-urlencoded'
             f'  |  user=svc_backup&recovery={enc}'),
            ("5", "0.061", "93.184.216.34", "10.0.0.5", "HTTP",
             "HTTP/1.1 200 OK  Content-Length: 17  (sync accepted)"),
            ("6", "0.090", "10.0.0.5", "8.8.8.8", "DNS",
             "Standard query A  cdn.example.com"),
        ]

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        pkts = self._packets(instance)

        if subpath.strip("/") == "download":
            text = "\n".join(f"#{n} {t}s {src} -> {dst} {proto}  {info}"
                             for n, t, src, dst, proto, info in pkts)
            return LabResult(text, content_type="text/plain; charset=utf-8",
                             headers={"Content-Disposition":
                                      "attachment; filename=capture.txt"})

        rows = "".join(
            f"<tr><td>{n}</td><td class='muted'>{t}</td><td>{src}</td><td>{dst}</td>"
            f"<td><b>{proto}</b></td><td class='mono' style='font-size:12px'>"
            f"{html.escape(info)}</td></tr>"
            for n, t, src, dst, proto, info in pkts
        )
        body = f"""
<h1>NetCapture</h1>
<p class="muted">A captured session (6 packets). Inspect each payload. One packet
   leaks a credential that isn't plaintext.</p>
<div class="card" style="overflow:auto">
  <table>
    <tr><th>#</th><th>Time</th><th>Source</th><th>Destination</th><th>Proto</th><th>Info / payload</th></tr>
    {rows}
  </table>
</div>
<div class="card">
  <h2>Decode bench</h2>
  <label>Paste a value to Base64-decode</label>
  <textarea id="in" rows="2"></textarea>
  <button class="ghost" onclick="var o;try{{o=decodeURIComponent(escape(atob(
    document.getElementById('in').value.trim())))}}catch(e){{o='[error]'}}
    document.getElementById('out').value=o;">Base64 decode</button>
  <label>Result</label><textarea id="out" rows="2" readonly></textarea>
</div>
<p class="muted">Download the raw capture: <a href="{base}/download">capture.txt</a>.
   The flag is a <code>MYCTF{{...}}</code> value once decoded.</p>"""
        return LabResult(self.page(instance, "NetCapture", body))
