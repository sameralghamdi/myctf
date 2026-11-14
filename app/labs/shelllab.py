"""Generic lab handler for terminal challenges (see shell_scenarios.py).

Endpoints under /labs/<instance>/ :
  GET  shell        -> {"user","host","home","cwd","motd"}   (terminal start-up)
  POST shell        -> {"stdout","stderr","cwd"}             body: {"command": "..."}
  GET  exec?cmd=    -> {"output","cwd"}                      (older combined form)
  GET  (anything)   -> a plain HTML terminal, for "open in tab"

The React <TerminalEmulator> uses the two `shell` endpoints. Commands are
interpreted by FakeShell: no real process is ever started.
"""
from __future__ import annotations

import json

from .. import limiter
from .base import LabHandler, LabResult, get_state
from .shell_scenarios import ShellScenario

MAX_COMMAND = 512
COMMANDS_PER_MINUTE = 120


def _json(payload: dict, status: int = 200) -> LabResult:
    return LabResult(json.dumps(payload), status=status, content_type="application/json")


class ShellLab(LabHandler):
    is_shell = True

    def __init__(self, scenario: ShellScenario):
        self.scenario = scenario
        self.kind = scenario.kind
        self.title = scenario.title

    def _state(self, instance) -> dict:
        st = get_state(instance["id"])
        if "shell" not in st:
            st["shell"] = self.scenario.build(instance["flag"])
            st["cwd"] = self.scenario.home
        return st

    def _session(self, st) -> dict:
        sc = self.scenario
        return {"user": sc.user, "host": sc.host, "home": sc.home,
                "cwd": st["cwd"], "motd": sc.motd}

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        st = self._state(instance)
        sub = subpath.strip("/")

        if sub in ("shell", "exec"):
            if sub == "shell" and request.method == "GET":
                return _json(self._session(st))
            if sub == "shell" and request.method != "POST":
                return _json({"error": "Use POST."}, 405)
            if sub == "exec":
                command = request.values.get("cmd", "")
            else:
                body = request.get_json(silent=True)
                command = body.get("command") if isinstance(body, dict) else None
            if not isinstance(command, str):
                return _json({"error": "command must be text"}, 400)
            if len(command) > MAX_COMMAND:
                return _json({"stdout": "", "cwd": st["cwd"],
                              "stderr": f"bash: command too long (max {MAX_COMMAND} characters)"})
            if not limiter.allow(f"shell:{instance['id']}", COMMANDS_PER_MINUTE, 60):
                return _json({"error": "Too many commands. Slow down a little."}, 429)
            result = st["shell"].run_ex(st["cwd"], command)
            st["cwd"] = result["cwd"]
            if sub == "exec":
                combined = "\n".join(x for x in (result["stdout"], result["stderr"]) if x)
                return _json({"output": combined, "cwd": result["cwd"]})
            return _json(result)

        return LabResult(self.page(instance, self.title, self._fallback_html(instance)))

    def _fallback_html(self, instance) -> str:
        sc, base = self.scenario, self.base_url(instance)
        prompt_js = json.dumps(f"{sc.user}@{sc.host}:")
        home_js = json.dumps(sc.home)
        return f"""
<h1>{sc.title}</h1>
<p class="muted">{sc.motd}</p>
<div class="card">
  <pre id="term" style="height:320px;overflow:auto"></pre>
  <form id="f"><input id="cmd" autocomplete="off" autofocus placeholder="type a command…"></form>
</div>
<script>
 var term=document.getElementById('term'), cwd={home_js};
 function prompt(){{term.append({prompt_js}+cwd.replace({home_js},'~')+'$ ');term.scrollTop=term.scrollHeight;}}
 prompt();
 document.getElementById('f').addEventListener('submit', async function(e){{
   e.preventDefault();
   var inp=document.getElementById('cmd'), cmd=inp.value; inp.value='';
   term.append(cmd+'\\n');
   var r=await fetch('{base}/shell',{{method:'POST',credentials:'same-origin',
     headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{command:cmd}})}});
   var d=await r.json();
   if(d.stdout) term.append(d.stdout+'\\n');
   if(d.stderr||d.error){{var s=document.createElement('span');s.className='err';
     s.textContent=(d.stderr||d.error)+'\\n';term.append(s);}}
   if(d.cwd) cwd=d.cwd;
   prompt();
 }});
</script>"""
