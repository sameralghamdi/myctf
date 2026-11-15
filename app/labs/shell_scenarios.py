"""Terminal ("shell") challenges, defined as data.

A ShellScenario describes one simulated machine: who you are, which files exist,
which are root-only, and which mock programs are installed. ``{flag}`` inside a
file is replaced with the player's own per-session flag when the lab starts.

Adding a terminal challenge = add a scenario here + a manifest in challenges/
whose ``lab_kind`` equals the scenario's ``kind``. No other code is needed.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import urlsplit

from .fakeshell import FakeShell, Program, printable


@dataclass(frozen=True)
class ShellScenario:
    kind: str                       # == challenge lab_kind
    title: str
    user: str
    host: str
    home: str
    motd: str                       # shown once when the terminal opens
    files: dict[str, str]
    root_only: frozenset = frozenset()
    sudo_nopasswd: tuple = ()
    # flag -> {program name or absolute script path: callable}
    programs: Callable[[str], dict[str, Program]] | None = None
    # flag -> extra files whose content is computed from the flag
    dynamic_files: Callable[[str], dict[str, str]] | None = field(default=None)

    def build(self, flag: str) -> FakeShell:
        files = {path: text.replace("{flag}", flag) for path, text in self.files.items()}
        if self.dynamic_files:
            files.update(self.dynamic_files(flag))
        return FakeShell(files, user=self.user, home=self.home, host=self.host,
                         root_only=set(self.root_only),
                         sudo_nopasswd=list(self.sudo_nopasswd),
                         programs=self.programs(flag) if self.programs else None)


# =========================================================== 1. linux basics ==
LINUX_BASICS = ShellScenario(
    kind="linux_basics", title="Terminal — Quiet Room",
    user="ctf", host="lab", home="/home/ctf",
    motd="Assigned host ready. Type help for terminal controls.",
    files={
        "/home/ctf/README.txt": "Welcome! Find the hidden flag in your home dir.",
        "/home/ctf/notes.txt": "TODO: tidy up. Nothing secret here.",
        "/home/ctf/.secret/flag.txt": "{flag}",
        "/etc/hostname": "linux-basics-lab",
    },
)

# ============================================================ 2. linux privesc ==
LINUX_PRIVESC = ShellScenario(
    kind="linux_privesc", title="Terminal — Higher Ground",
    user="ops", host="lab", home="/home/ops",
    motd="Assigned host ready. Type help for terminal controls.",
    files={
        "/home/ops/notes.txt": "Deploy scripts live in /opt. Ask admin for root.",
        "/root/flag.txt": "{flag}",
        "/root/.bash_history": "ls\ncat flag.txt\nexit",
        "/etc/hostname": "privesc-lab",
    },
    root_only=frozenset({"/root/flag.txt", "/root/.bash_history"}),
    sudo_nopasswd=("/usr/bin/cat",),
)


# ================================================== 3. web recon (mock curl) ==
_WEB_HOST = "10.10.10.5"
_WEB_USER, _WEB_PASS = "admin", "S3cur3_B4ckup!"

_WEB_PAGES = {
    "/": ("text/html",
          "<html>\n  <head><title>Intranet Portal</title></head>\n  <body>\n"
          "    <h1>Intranet Portal</h1>\n    <p>Staff only. Please sign in.</p>\n"
          "    <!-- TODO(dev): clean up robots.txt before go-live -->\n  </body>\n</html>"),
    "/robots.txt": ("text/plain",
                    "User-agent: *\nDisallow: /backup/\nDisallow: /admin/"),
    "/backup/": ("text/html",
                 "<html><body><h1>Index of /backup/</h1>\n<pre>\n"
                 "<a href=\"config.php.bak\">config.php.bak</a>      2024-03-02 09:14   312\n"
                 "</pre></body></html>"),
    "/backup/config.php.bak": ("text/plain",
                               "<?php\n// Portal configuration (backup copy)\n"
                               "$db_host    = \"127.0.0.1\";\n"
                               f"$admin_user = \"{_WEB_USER}\";\n"
                               f"$admin_pass = \"{_WEB_PASS}\";\n?>"),
}


def _web_programs(flag: str) -> dict[str, Program]:
    def curl(shell, args, stdin, as_root):
        show_headers, creds, url = False, None, None
        it = iter(args)
        for a in it:
            if a in ("-i", "--include"):
                show_headers = True
            elif a in ("-u", "--user"):
                creds = next(it, "")
            elif a in ("-H", "--header"):
                header = next(it, "")
                if header.lower().startswith("authorization: basic "):
                    try:
                        creds = base64.b64decode(header.split()[-1]).decode()
                    except Exception:
                        creds = ""
            elif a.startswith("-"):
                continue                      # -s, -v, -k … accepted and ignored
            else:
                url = a
        if not url:
            return "", "curl: try 'curl --help' for more information"
        parts = urlsplit(url if "://" in url else "http://" + url)
        if parts.hostname != _WEB_HOST:
            return "", f"curl: (6) Could not resolve host: {parts.hostname or url}"
        path = parts.path or "/"

        if path in ("/admin", "/admin/"):
            if creds == f"{_WEB_USER}:{_WEB_PASS}":
                status, ctype = "200 OK", "text/html"
                body = ("<html><body>\n  <h1>Admin console</h1>\n"
                        f"  <p>Welcome back, admin.</p>\n  <p>Flag: {flag}</p>\n</body></html>")
            else:
                status, ctype = "401 Unauthorized", "text/html"
                body = "<html><body><h1>401 Unauthorized</h1></body></html>"
        elif path in _WEB_PAGES:
            status = "200 OK"
            ctype, body = _WEB_PAGES[path]
        elif path == "/backup":
            status, ctype, body = "301 Moved Permanently", "text/html", ""
        else:
            status, ctype = "404 Not Found", "text/html"
            body = "<html><body><h1>404 Not Found</h1></body></html>"

        if show_headers:
            head = [f"HTTP/1.1 {status}", "Server: nginx/1.24.0",
                    f"Content-Type: {ctype}", f"Content-Length: {len(body)}"]
            if status.startswith("401"):
                head.append('WWW-Authenticate: Basic realm="Admin"')
            if status.startswith("301"):
                head.append("Location: /backup/")
            body = "\n".join(head) + "\n\n" + body
        return body, ""

    return {"curl": curl}


WEB_RECON = ShellScenario(
    kind="shell_web_recon", title="Terminal — Internal Affairs",
    user="guest", host="kali-web", home="/home/guest",
    motd=f"Target in scope: http://{_WEB_HOST}  -  read README.txt to begin.",
    files={
        "/home/guest/README.txt": (
            "ENGAGEMENT BRIEF\n"
            f"Target : http://{_WEB_HOST}  (intranet portal)\n"
            "Goal   : get into the admin console and read the flag.\n"
            "Tools  : curl is installed. Try:  curl http://" + _WEB_HOST + "/\n"
            "Tip    : developers often forget what they told search engines to ignore."),
        "/home/guest/scope.txt": f"{_WEB_HOST}  # only this host is in scope",
    },
    programs=_web_programs,
)


# ============================================ 4. packet forensics + decoder ==
_XOR_KEY = "k4li-r0cks"

_DECODER_SOURCE = '''#!/usr/bin/env python3
"""decode.py - undo the attacker's exfil encoding.

usage: ./decode.py <base64-data> <key>

The malware XORs the stolen text with a repeating key, then base64-encodes it.
"""
import base64, sys

data = base64.b64decode(sys.argv[1])
key = sys.argv[2].encode()
print(bytes(b ^ key[i % len(key)] for i, b in enumerate(data)).decode(errors="replace"))
'''


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _exfil(flag: str) -> str:
    return base64.b64encode(_xor(flag.encode(), _XOR_KEY.encode())).decode()


def _packets(flag: str) -> list[tuple[str, str]]:
    a, s = "10.10.10.23", "10.10.10.5"
    row = "{n:>3} {t:>9} {src:<12} → {dst:<12} {proto:<5} {info}"
    data = [
        ("0.000000", a, s, "FTP", "Request: USER backup"),
        ("0.041882", s, a, "FTP", "Response: 331 Please specify the password."),
        ("0.090114", a, s, "FTP", f"Request: PASS {_XOR_KEY}"),
        ("0.133907", s, a, "FTP", "Response: 230 Login successful."),
        ("1.204551", a, "10.10.10.1", "DNS", "Standard query 0x3f1a A updates.kali-mirror.net"),
        ("1.250318", "10.10.10.1", a, "DNS", "Standard query response 0x3f1a A 203.0.113.80"),
        ("2.002761", a, "203.0.113.80", "HTTP", "GET /index.html HTTP/1.1"),
        ("2.118040", "203.0.113.80", a, "HTTP", "HTTP/1.1 200 OK  (text/html)"),
        ("3.560233", a, "203.0.113.80", "HTTP",
         f"POST /upload.php HTTP/1.1  (application/x-www-form-urlencoded)  data={_exfil(flag)}"),
        ("3.671902", "203.0.113.80", a, "HTTP", "HTTP/1.1 200 OK  (text/plain)"),
    ]
    return [(proto.lower(), row.format(n=i, t=t, src=src, dst=dst, proto=proto, info=info))
            for i, (t, src, dst, proto, info) in enumerate(data, 1)]


def _pcap_programs(flag: str) -> dict[str, Program]:
    def tshark(shell, args, stdin, as_root):
        capture, display_filter = None, ""
        it = iter(args)
        for a in it:
            if a == "-r":
                capture = next(it, None)
            elif a in ("-Y", "-R"):
                display_filter = next(it, "").lower()
        if not capture:
            return "", "tshark: no capture file given. Usage: tshark -r <file> [-Y <filter>]"
        if posixpath_base(capture) != "capture.pcap":
            return "", f"tshark: The file \"{capture}\" doesn't exist."
        rows = _packets(flag)
        if display_filter:
            wanted = [p for p in ("ftp", "dns", "http") if p in display_filter]
            if not wanted:
                return "", f"tshark: \"{display_filter}\" is not a filter this lab supports (try ftp, dns, http)."
            rows = [r for r in rows if r[0] in wanted]
            if "post" in display_filter:
                rows = [r for r in rows if "POST" in r[1]]
        return "\n".join(text for _, text in rows), ""

    def decode(shell, args, stdin, as_root):
        if len(args) != 2:
            return "", "usage: ./decode.py <base64-data> <key>"
        try:
            raw = base64.b64decode(args[0], validate=True)
        except Exception:
            return "", "decode.py: error: first argument is not valid base64"
        if not args[1]:
            return "", "decode.py: error: key must not be empty"
        return printable(_xor(raw, args[1].encode())), ""

    return {"tshark": tshark, "/home/analyst/decode.py": decode}


def posixpath_base(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _pcap_files(flag: str) -> dict[str, str]:
    # What `strings` / `cat` show for the "binary" capture: readable fragments only.
    return {"/home/analyst/evidence/capture.pcap": "\n".join([
        "\u00d4\u00c3\u00b2", "USER backup", f"PASS {_XOR_KEY}", "230 Login successful.",
        "updates.kali-mirror.net", "GET /index.html HTTP/1.1", "Host: updates.kali-mirror.net",
        "POST /upload.php HTTP/1.1", "Content-Type: application/x-www-form-urlencoded",
        f"data={_exfil(flag)}", "HTTP/1.1 200 OK"])}


PCAP_FORENSICS = ShellScenario(
    kind="shell_pcap_forensics", title="Terminal — Outbound",
    user="analyst", host="kali-web", home="/home/analyst",
    motd="Incident IR-2291: a workstation leaked data. Start with case-notes.txt.",
    files={
        "/home/analyst/case-notes.txt": (
            "CASE IR-2291\n"
            "Workstation 10.10.10.23 sent data to an unknown server.\n"
            "Evidence : evidence/capture.pcap\n"
            "Tools    : tshark -r <file> [-Y ftp|dns|http]   and   ./decode.py\n"
            "Intel    : this malware family XORs stolen text with a key, then base64s it.\n"
            "           Operators are lazy: the key is usually a password they already used."),
        "/home/analyst/decode.py": _DECODER_SOURCE,
    },
    programs=_pcap_programs,
    dynamic_files=_pcap_files,
)


SCENARIOS: tuple[ShellScenario, ...] = (
    LINUX_BASICS, LINUX_PRIVESC, WEB_RECON, PCAP_FORENSICS,
)
