"""Command Injection — network diagnostics tool over a SIMULATED shell.

Safety choice: user input is NEVER handed to a real shell or subprocess. Instead
a tiny, sandboxed command interpreter models just enough shell behaviour
(command separators ``;`` ``|`` ``&&``, and a handful of fake commands) to make
injection demonstrable and deterministic, with zero risk to the host.

The intended "app" runs ``ping -c 1 <host>``. Because it concatenates user input,
an attacker can append commands. The simulated filesystem contains ``flag.txt``.

Intended solution: host value like ``127.0.0.1; cat flag.txt`` (or ``| cat flag.txt``)
makes the simulator run the extra command and print the flag.

Remediation: never build shell strings from input; pass arguments as an argv
array to exec without a shell, and validate/allow-list the host.
"""
from __future__ import annotations

import html
import re
import shlex

from .base import LabHandler, LabResult


class CommandInjectionLab(LabHandler):
    kind = "command_injection"
    title = "NetTools — Connectivity Check"

    SEP = re.compile(r"\s*(?:;|\|\||&&|\|)\s*")

    def _fakefs(self, instance) -> dict:
        return {
            "flag.txt": instance["flag"],
            "readme.txt": "NetTools v0.9 - internal connectivity checker.",
            "/etc/hostname": "nettools-lab",
        }

    def _run_sim(self, instance, full_command: str) -> str:
        """Interpret a small subset of shell against the fake fs. No real exec."""
        fs = self._fakefs(instance)
        parts = [p for p in self.SEP.split(full_command) if p.strip()]
        out_lines: list[str] = []
        for part in parts:
            try:
                tokens = shlex.split(part)
            except ValueError:
                tokens = part.split()
            if not tokens:
                continue
            cmd, args = tokens[0], tokens[1:]
            if cmd == "ping":
                host = args[-1] if args else "(none)"
                out_lines.append(
                    f"PING {host}: 1 packets transmitted, 1 received, 0% packet loss")
            elif cmd == "cat":
                for a in args:
                    out_lines.append(fs.get(a, f"cat: {a}: No such file or directory"))
            elif cmd == "ls":
                out_lines.append("  ".join(k for k in fs if "/" not in k))
            elif cmd in ("id", "whoami"):
                out_lines.append("uid=1000(nettools) gid=1000(nettools)"
                                 if cmd == "id" else "nettools")
            elif cmd == "echo":
                out_lines.append(" ".join(args))
            else:
                out_lines.append(f"{cmd}: command not found")
        return "\n".join(out_lines)

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        base = self.base_url(instance)
        host = request.values.get("host", "")
        result_block = ""
        if host:
            # --- VULNERABLE: user input concatenated into the command line ---
            full = "ping -c 1 " + host
            output = self._run_sim(instance, full)
            result_block = (
                f'<div class="card"><h2>$ {html.escape(full)}</h2>'
                f'<pre>{html.escape(output)}</pre></div>'
            )

        body = f"""
<h1>NetTools — Connectivity Check</h1>
<p class="muted">Enter a host to ping from the lab server.</p>
<div class="card">
  <form method="get" action="{base}/">
    <label>Host</label>
    <input name="host" value="{html.escape(host)}" autofocus
           placeholder="example.com">
    <button type="submit">Run ping</button>
  </form>
</div>
{result_block}
<p class="muted">The server runs <code>ping -c 1 &lt;host&gt;</code> with your input
   appended directly. The sandbox also has a file called <code>flag.txt</code>.</p>"""
        return LabResult(self.page(instance, "NetTools", body))
