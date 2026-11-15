# MyCTF — Interactive Penetration Testing & Cybersecurity Training Platform

> **Learn. Exploit. Capture.**

MyCTF is a hands-on Capture-The-Flag learning platform. Users exploit
**intentionally vulnerable, isolated lab targets** — real SQL injection, XSS,
IDOR, path traversal, command injection, and more — capture per-session flags,
and then read a debrief explaining the root cause and the fix.

It is a training environment in the same family as DVWA, OWASP WebGoat and the
PortSwigger Web Security Academy: every vulnerability lives inside a sandboxed
teaching target, never in the platform itself, and never pointed at real
third-party systems.

```
Learn → Start Lab → Investigate → Exploit → Capture Flag → Understand → Improve
```

---

## What this repository contains

A **fully runnable, fully tested** implementation of the platform core and 37
interactive challenges, built on a deliberately dependency-light stack
(**Flask + SQLite + Python stdlib crypto**) so it runs and passes its test suite
anywhere, with **no infrastructure to provision**.

The production target (Next.js / FastAPI / PostgreSQL / Redis / Docker-orchestrated
labs / microVMs) is documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
and the code is structured around the two seams (`app/models.py`,
`app/labs/__init__.py`) you swap to get there.

> **Why Flask + SQLite and not the FastAPI/Docker stack described in the spec?**
> The same application logic is implemented here on a stack that is 100% runnable
> and testable without Docker or a database server. Per the project's own rule —
> *"If an infrastructure feature cannot safely run in the current development
> environment, provide a working local implementation and clearly document what is
> needed for secure deployment"* — the ephemeral-container / microVM isolation is
> documented as the deployment target while the dev build provides equivalent
> **logical** isolation (per-user, per-session instances; unguessable routing
> tokens; ownership checks; backend-only flag validation).

### Original engines (maintainer reference)

| # | Challenge | Category | Difficulty | Live lab | Verified by |
|---|-----------|----------|-----------|:--------:|-------------|
| 1 | HTTP Basics | Web | Very Easy | ✅ | `test_http_basics` |
| 2 | Encoding & Decoding | Crypto | Very Easy | ✅ | `test_encoding_decoding` |
| 3 | SQL Injection — Login Bypass | Web | Easy | ✅ | `test_sqli_login_bypass` |
| 4 | Reflected XSS | Web | Easy | ✅ | `test_reflected_xss` |
| 5 | IDOR — Broken Object Access | Web | Easy | ✅ | `test_idor_profile_access` |
| 6 | Path Traversal | Web | Easy | ✅ | `test_path_traversal` |
| 7 | Command Injection | Web | Medium | ✅ | `test_command_injection` |
| 8 | Stored XSS | Web | Medium | ✅ | `test_stored_xss` |
| 9 | Insecure File Upload | Web | Medium | ✅ | `test_insecure_file_upload` |
| 10 | Weak Password Reset | Web | Medium | ✅ | `test_weak_password_reset` |
| 11 | JWT Authorization Flaw | Web | Medium | ✅ | `test_jwt_alg_none` |
| 12 | API — Broken Object Authorization | API | Medium | ✅ | `test_api_bola` |
| 13 | PCAP Investigation | Forensics | Easy | ✅ | `test_pcap_investigation` |
| 14 | Basic Linux Commands | Linux | Very Easy | ✅ | `test_linux_basics` |
| 15 | Linux Permission Misconfiguration | PrivEsc | Medium | ✅ | `test_linux_privesc` |

Every challenge above has an **end-to-end test that performs the intended exploit
against the live lab, captures the per-session flag, submits it, and asserts the
award** — a challenge is not counted as done unless its test passes.

Two new live-lab engines were added alongside these: a safe **simulated shell**
(`app/labs/fakeshell.py`) backing the browser-terminal Linux challenges, and a
reused XSS execution checker for the stored-XSS moderator simulation.

### Discovery-first challenges and web targets

The project contains **37 challenges**: the original 17 plus 20 EWPT scenarios.
All challenge names, briefs and public URLs are neutral. Objectives, exam-topic
text and resources are absent from the player challenge pages. Versions,
software stacks, vulnerable parameters and solution steps are discovered inside
the targets. Optional hints remain locked until requested; solution debriefs
unlock after a solve.

**16 EWPT HTTP targets** have browser interfaces alongside the existing terminal.
Click **Target page** or **Terminal** to switch. Both interfaces share the same
instance, flag and mutable target state. Tomcat, sign-in, shopping, password reset,
API documentation, default server pages and directory listings each have their
own interface. The target browser includes navigation, **Source**, **Headers**
and an **Edit request** panel for methods, headers and request bodies.

These are local training reproductions. They do not install or operate the real
Apache/Tomcat/FastAPI/nginx products. SSH, RDP and virtual archives retain the
simulated terminal model. No external targets or DNS setup are needed.

See [web and terminal guide](docs/EWPT_TERMINALS.md) for setup and supported
behavior. `tests/test_ewpt.py` solves all 20 EWPT scenarios;
`tests/test_ewpt_web.py` checks browser/terminal state sharing, authentication,
source-only evidence, neutral metadata, isolation, reset and input validation.

Platform features implemented: registration / login / logout, JWT-over-sessions
auth with revocation, password reset, email-verification flow, optional TOTP 2FA,
RBAC (student / instructor / administrator), dashboard with skill breakdown,
challenge catalog, split-screen play screen with live lab iframe, server-side
flag validation with award-once scoring, three-level hints with point deductions,
leaderboard, learning paths, achievements, profile, admin panel (manifest
validate/publish, user roles, running-lab monitor + restart, audit log,
analytics), and a lab orchestrator with start/stop/reset/auto-expiry.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the remaining seed challenges and
later phases (competitions/teams UI, forensics/network/privesc labs).

---

## Quick start

Requirements: **Python 3.11+**. No database server, no Docker, no Node needed for
the dev build.

```bash
cd myctf
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt                       # Flask, PyJWT, PyYAML, pytest
python run.py
```

Open <http://127.0.0.1:8000>.

- A bootstrap admin (`admin`) is created on first run. There is no default
  password: set `MYCTF_ADMIN_PASSWORD`, or read the random one printed once in
  the terminal on first start.
- Register a student account from the UI, open **Challenges**, pick one, click
  **Start Lab**, exploit the target in the right-hand pane, and submit the flag.

### Run the tests

```bash
python -m pytest -q          # 40 tests: auth, scoring, isolation, and an
                             # end-to-end solve for every seed challenge
```

### Configuration

All settings have safe dev defaults; override via environment or a `.env` file
(see [`.env.example`](.env.example)). **Always set `MYCTF_SECRET_KEY` outside
local development** — it signs auth tokens and keys flag hashing.

---

## How it fits together

```
app/
  __init__.py        app factory: wiring, schema init, seeding, error handlers
  config.py          configuration (env-driven)
  db.py              SQLite connection management
  models.py          data-access layer  ← swap here for PostgreSQL/SQLAlchemy
  security.py        PBKDF2 hashing, JWT, flag HMAC, stdlib TOTP
  manifest.py        challenge manifest validation (the publish safety gate)
  scoring.py         authoritative flag validation + award-once scoring
  seed.py            idempotent seeding from challenge manifests
  limiter.py         in-process rate limiter  ← swap here for Redis
  auth/              register/login/logout/reset/2FA + RBAC decorators
  core/              dashboard, catalog, play screen, submit, hints, leaderboard
  admin/             admin panel + manifest publish workflow
  labs/              ← the ONLY place vulnerable targets live
    __init__.py      orchestrator: start/stop/reset/expire  ← swap for containers
    base.py          lab handler base + per-instance state
    registry.py      lab_kind → handler
    routes.py        /labs blueprint (ownership-checked, isolated)
    sqli.py xss.py idor.py traversal.py cmdinjection.py httpbasics.py crypto.py
  templates/ static/ dark-red themed UI (theme.css tokens + app.css components)
challenges/          versioned YAML manifests (one per challenge)
tests/               pytest: e2e solves + isolation + scoring + auth
docs/                ARCHITECTURE, ADDING_CHALLENGES, SECURITY, ROADMAP
schema.sql           full database schema
```

Read [`docs/ADDING_CHALLENGES.md`](docs/ADDING_CHALLENGES.md) to add a challenge,
and [`docs/SECURITY.md`](docs/SECURITY.md) for the isolation model and the safety
decisions (e.g. why the command-injection lab uses a simulated interpreter).

---

## Safety & responsible use

MyCTF generates intentionally vulnerable targets **for training inside the
platform only**. Do not use these techniques against systems you do not own or
lack written permission to test. All users, companies, and data in the labs are
synthetic.
