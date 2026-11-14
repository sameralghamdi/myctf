# Security model & safety decisions

MyCTF deliberately runs vulnerable code. This document explains how that is kept
safe, and the specific choices made so the dev build is harmless to its host.

## Principles

1. **Vulnerable code is quarantined.** It exists only in `app/labs/*` handlers,
   served only under `/labs`. The platform's auth, API, admin and database code
   contain no intentional vulnerabilities.
2. **The platform stays secure even when a lab is fully exploited.** Capturing a
   lab flag grants nothing on the platform: flags are validated by the backend,
   bound to the exploiting user's own instance, and award points at most once.
3. **No real-world targets, ever.** All users, companies and data are synthetic.
   Labs have no outbound network and (in production) no host/metadata access.

## Platform hardening (dev build)

- **Passwords**: PBKDF2-HMAC-SHA256, 600k iterations, per-user salt, constant-time
  verify. (Production: Argon2id — single-interface swap in `security.py`.)
- **Auth tokens**: JWT (HS256) whose `jti` references a server-side `sessions`
  row, so logout and expiry truly revoke access. Delivered as an HttpOnly,
  SameSite=Lax cookie (set `secure=True` behind TLS) and accepted as a Bearer
  token for API clients.
- **Flags**: static flags stored as HMAC-SHA256; all flag comparison is
  constant-time (`hmac.compare_digest`).
- **Password reset / email verification**: one-time tokens stored **hashed**, with
  expiry and single-use; reset responses don't reveal whether an email exists.
- **RBAC**: `student` / `instructor` / `administrator`, enforced by decorators.
- **Rate limiting**: flag submissions and logins are throttled per user/window.
- **Audit log**: logins, solves, hint unlocks, lab lifecycle and admin actions.
- **Input validation**: usernames, emails and password strength are validated;
  manifests are validated and unsafe ones rejected before publish.

## Why some labs are *simulated* (and why that's the right call)

Two targets would, implemented naïvely, run attacker-controlled input against the
real host. They are modelled safely instead — which is both safer and
deterministic for automated tests:

- **Command Injection** (`labs/cmdinjection.py`): user input is **never** passed
  to a real shell or `subprocess`. A tiny sandboxed interpreter models just enough
  shell behaviour (`;`, `|`, `&&`, and a handful of fake commands) over an
  in-memory fake filesystem. The learner still discovers and performs a genuine
  injection (breaking out of `ping -c 1 <host>`), but nothing executes on the host.
- **Path Traversal** (`labs/traversal.py`): the vulnerable `join`+`normpath` is
  real, but it resolves against an **in-memory virtual filesystem** (a dict), so
  `../` traversal is demonstrable while the host filesystem is never touched.

- **Reflected XSS** (`labs/xss.py`): the proof-of-execution is **harmless** — the
  learner must craft a payload that would call a benign `myctfSolve()` function.
  No cookie theft or exfiltration is required or taught. A server-side checker
  recognises a payload that would execute and reveals the flag.

- **SQL Injection** (`labs/sqli.py`): a genuine string-concatenated query runs
  against a throwaway **in-memory SQLite database seeded with synthetic users**,
  created fresh per instance and closed on teardown. Real injection, zero blast
  radius.

- **IDOR** (`labs/idor.py`): a real missing-authorization bug over synthetic
  in-memory accounts.

## Production isolation (required for deployment)

The dev build provides *logical* isolation. A real deployment must add
*infrastructure* isolation for the lab tier — ephemeral containers / Firecracker
microVMs with dropped capabilities, read-only FS, no host mounts, no Docker
socket, egress-blocked network, null-routed cloud metadata, and CPU/memory/pids
quotas. See [`ARCHITECTURE.md`](ARCHITECTURE.md) §3.

## Reporting

This is a training platform; treat intentional vulnerabilities in `app/labs/*` as
by-design. Security issues in the **platform** code (auth, scoring, isolation
boundary, manifest validation) are real bugs — fix with an accompanying test in
`tests/test_isolation.py`.
