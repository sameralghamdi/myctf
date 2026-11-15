# Roadmap — honest status

This build implements the **foundation + first working labs** against the spec's
6-phase plan, with everything that is marked done covered by passing tests. The
items below are **not yet implemented** and are listed so nothing is mistaken for
complete.

## Done (Phases 1–4 + all 15 seed challenges)

- Project structure, DB schema, idempotent seeding.
- Auth (register/login/logout/reset/verify), optional TOTP 2FA, RBAC, sessions.
- Dashboard, skill breakdown, catalog, split-screen play screen, dark-red UI.
- Lab orchestrator: start / stop / reset / auto-expiry, per-user limits.
- **All 15 interactive, individually-tested seed challenges** across Web, Crypto,
  API, Forensics, Linux and PrivEsc — including the browser-terminal Linux labs
  over a safe simulated shell (`app/labs/fakeshell.py`).
- Server-side flag validation, award-once scoring, first-blood, hints w/ cost.
- Leaderboard, learning paths, achievements, profile.
- Admin panel: manifest validate/publish, user roles, running-lab monitor +
  restart, audit log, analytics API.
- **50 automated tests**: e2e solves (one per challenge), isolation, scoring, auth.

## Later phases

- **Phase 5 — Competitions & teams**: schema tables exist (`competitions`,
  `teams`, `team_members`, `score_events`); the admin CRUD UI, team registration,
  event scoreboard, score freeze and dynamic scoring are not yet built.
- **Network / OS / privesc labs** needing real OS behaviour: require the
  container/microVM lab tier from `ARCHITECTURE.md` and a browser terminal
  (xterm.js) wired to an isolated shell.
- **Production stack migration**: FastAPI + PostgreSQL/SQLAlchemy + Redis +
  container orchestrator, behind the two seams described in `ARCHITECTURE.md`.
- **Next.js frontend**: the current UI is server-rendered (Jinja); a Next.js SPA
  can consume the existing JSON API unchanged.
