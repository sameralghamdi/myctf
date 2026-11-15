# EWPT terminal challenges

20 new challenges (101–120) join the original 17. Search **EWPT** in Challenges,
open a challenge, click **Start lab**, then enter `cat README.txt`. The same
terminal component, command history, flag submission, hints, scoring, ownership,
expiry, stop and restart controls used by the original labs apply here.

## Install the update

Use this archive as the complete updated project, or copy these additions and
changes into your current checkout:

- `challenges/101-*.yaml` through `challenges/120-*.yaml`
- `app/labs/ewpt.py`
- Updated `app/labs/registry.py` and `app/labs/fakeshell.py`
- `tests/test_ewpt.py`, this guide and the README

Keep your current `.env` and `instance/` database. Stop the backend, update the
files, then restart using your existing startup command. `create_app()` seeds the
new manifests automatically and updates matching challenge slugs. Existing
accounts and solves remain in the database. No schema migration or additional
Python dependency is needed. Restarting the in-process backend clears active
terminal state, as with the original terminal labs.

For a fresh local setup:

```bash
cd myctf
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

To use the React frontend, in a second terminal:

```bash
cd myctf/frontend
npm install
npm run dev
```

Open the local URL printed by Vite. The existing Flask-rendered interface also
works directly at http://127.0.0.1:8000.

## Collection

| # | Challenge | Terminal tools / evidence |
|---|---|---|
| 101 | Fuzz the Login | ffuf, SQL payload list, curl session cookies |
| 102 | HTTP Method Mayhem | curl OPTIONS, PUT, GET; per-lab uploaded files |
| 103 | Coupon King | Repeated coupons or negative quantity, checkout |
| 104 | Vendor OSINT | HTML comment, `answer <service>` |
| 105 | FastAPI Docs Leak | OpenAPI schema and required header |
| 106 | Stack Fingerprint | Headers, robots.txt, leaked source |
| 107 | Apache 2.4.49 Traversal | Encoded traversal, curl --path-as-is |
| 108 | Tomcat Weak Credentials | HTTP Basic authentication, HTML source |
| 109 | Nginx Alias Traversal | Off-by-slash alias path |
| 110 | DNS Enumeration | nmap, dig TXT / CHAOS records |
| 111 | SSH Key Leak | curl download, chmod 600, simulated SSH |
| 112 | XRDP Exposure | nmap, simulated xfreerdp, mounted Desktop files |
| 113 | Digest Auth Realm | curl --digest, response headers |
| 114 | Backup File Leak | ffuf, curl download, virtual unzip |
| 115 | API Endpoint Fuzzing | ffuf status filters, forwarding header |
| 116 | Password Reset Step Skip | Reset API, login and session cookie |
| 117 | Architecture Mapping | nmap, `answer <architecture>` |
| 118 | Log Analysis | access.log, awk / sort / uniq, `answer <ip>` |
| 119 | SQL Injection via Fuzzing | ffuf, ORDER BY, UNION SELECT |
| 120 | HTTP TRACE Leak | OPTIONS, TRACE, reflected headers |

## Supported commands

The existing built-ins (`ls`, `cd`, `cat`, `grep`, `find`, `head`, `tail`,
`strings`, `base64` and others) remain available. Type `help` to see the specific
tools installed in each lab. Commands run individually; pipes are supported,
but shell redirection, `;`, `&&` and command substitution are unsupported.

HTTP labs provide `curl` with `-i`, `-I`, `-X`, `-H`, `-d`, `--data`,
`--data-raw`, `--data-binary`, `--data-urlencode`, `--json`, `-u`, `--digest`,
`-b`, `-c`, `-o`, `-O` and `--path-as-is`. Form and JSON requests are accepted.
Download with `-o` or `-O`; use `-c cookies.txt` to save a login session and
`-b cookies.txt` to reuse it. Files are relative to the current terminal directory.
The curl cookie jar is a simplified lab format, not a browser/Netscape cookie file.

`ffuf` reads the supplied virtual wordlist and evaluates each candidate against
the simulated target. It supports `-u`, `-w`, `-X`, `-d`, `-H`, `-mc`, `-fc`,
`-fs` and `-ms`, with one `FUZZ` placeholder keyword. Requests are capped at 256
wordlist entries per invocation. Find the bundled lists with `ls`.

```bash
ffuf -u http://login.lab.local/api/login -X POST -d 'username=FUZZ&password=test' -w sqli-payloads.txt -mc 200
ffuf -u http://api-fuzz.lab.local/api/FUZZ -w api-wordlist.txt -mc 200,403
```

Only relevant tools are installed: `dig` in DNS, `ssh` / `chmod` in SSH,
`xfreerdp` in XRDP, and `unzip` in the backup lab. Log analysis supports the
specific `awk '{print $1}'` expression plus `sort`, `sort -nr` and `uniq -c`.
For OSINT, architecture and log analysis, enter the evidence-derived answer using
`answer` to receive a unique session flag rather than a shared static flag.

## Simulation boundaries

Everything operates in memory: no player command starts a process, reads the
server filesystem or connects to an external machine. The `.lab.local` names
are interpreted only by the simulated terminal; opening them in your browser,
Burp, a real shell or an external scanner will not connect to these targets.
Tools implement the documented training subset, not the full external programs.

SQL challenges execute their deliberately unsafe SELECT against a fresh
in-memory SQLite database containing only synthetic challenge data. They never
query the platform database. Other HTTP targets model the intended behavior
rather than running Apache, Tomcat, FastAPI or nginx servers.

SSH uses an opaque virtual key and requires `chmod 600` before authentication;
it then mounts the simulated remote home. RDP mounts a virtual Desktop after
successful authentication; it does not render a desktop. `www.zip` is a virtual
archive understood by the lab's `unzip`, not a downloadable binary ZIP file.
Digest authentication models `curl --digest` credentials, not a cryptographic
Digest handshake. Nmap reports the scenario's preset services.

All mutable target state and flags belong to one lab instance. Restart creates a
fresh flag and discards uploaded files, cookies, coupon state, passwords and
mounted files. Old flags are rejected after restart.

## Verification

```bash
python -m pytest
```

`tests/test_ewpt.py` covers all 20 intended solutions through the terminal and
flag-submission API, unsuccessful attempts, real wordlist selection and filters,
coupon replay, download paths, SSH permission checks, ownership, scope rejection
and reset isolation. The original tests remain in place.
