# MyCTF Architecture

This document describes both the **runnable dev build** in this repository and the
**production target** it is designed to grow into. The two share the same domain
logic; they differ in the infrastructure behind two well-defined seams.

---

## 1. Components

### Dev build (this repo — runnable with zero infrastructure)

```
            ┌─────────────────────────────────────────────┐
  Browser → │  Flask app (single process)                 │
            │   ├─ /            platform UI (Jinja)        │
            │   ├─ /api/*       JSON API                   │
            │   ├─ /admin/*     admin panel                │
            │   └─ /labs/<id>/* ISOLATED vulnerable targets│
            │  SQLite (file)   in-process lab state        │
            │  in-process rate limiter + lab sweeper       │
            └─────────────────────────────────────────────┘
```

### Production target

```
                    ┌────────────┐
        Browser  →  │  Next.js    │  (SPA/SSR frontend)
                    └─────┬───────┘
                          │  HTTPS
                   ┌──────▼───────┐        ┌─────────────┐
                   │  Reverse      │        │ PostgreSQL  │
                   │  proxy (TLS)  │        └─────────────┘
                   └──┬────────┬───┘        ┌─────────────┐
                      │        │            │ Redis       │ cache, queues,
         ┌────────────▼──┐  ┌──▼──────────┐ └─────────────┘ rate limits
         │ MyCTF API      │  │ Lab router  │
         │ (FastAPI)      │  │ (per-instance routing by token)
         └──────┬─────────┘  └──┬──────────┘
                │ enqueue        │ proxied, network-isolated
         ┌──────▼─────────┐  ┌───▼───────────────────────────┐
         │ Lab orchestrator│→ │ Ephemeral labs:                │
         │ (worker)        │  │  • Docker containers (web labs)│
         └─────────────────┘  │  • Firecracker microVMs        │
                              │    (network/OS/privesc labs)    │
                              └────────────────────────────────┘
```

The MyCTF API, PostgreSQL and secrets live in a **trusted** network. Lab
instances live in an **untrusted**, segmented network and can reach neither.

---

## 2. The two seams

Everything that must change between dev and production is behind two modules:

| Seam | Dev implementation | Production implementation |
|------|--------------------|---------------------------|
| **Data access** — `app/models.py` + `app/db.py` | SQLite via stdlib `sqlite3`; `schema.sql` defines tables | PostgreSQL via SQLAlchemy 2.0; Alembic migrations generated from the same schema |
| **Lab orchestration** — `app/labs/__init__.py` | In-process handler state keyed by instance id | Container/microVM controller: `start()` provisions an isolated instance and returns a routable, network-isolated URL |

Because all SQL is confined to the data-access layer and all lab lifecycle to the
orchestrator, these swaps are localized rather than a rewrite. The HTTP handlers,
scoring, auth, manifests and UI are unchanged.

---

## 3. Lab isolation model

### Requirement (from the spec)

> Never place intentionally vulnerable endpoints inside the production
> application's own API or authentication system. No access from a lab to the
> host filesystem / production DB / secrets / internet / cloud metadata. No
> privileged containers. No Docker socket. CPU/memory limits. Network
> segmentation. Automatic expiration & cleanup. Per-session flags. Flag
> validation on the secure backend.

### How the dev build satisfies the *logical* half of this

- **Separation**: all vulnerable code lives only under the `/labs` blueprint and
  the `app/labs/*` handlers — never in `auth/`, `core/` or `admin/`.
- **Per-user, per-session instances**: `lab_instances` is keyed `UNIQUE(user,
  challenge)`; each carries its own randomly-generated flag.
- **Unguessable routing token**: the instance id (`secrets.token_hex(16)`) is the
  only way to address a lab and is also ownership-checked on every request — a
  user cannot reach another user's instance (returns 403). Tested in
  `tests/test_isolation.py`.
- **Backend-only flag validation**: exploiting a lab merely *reveals* a flag;
  `app/scoring.py` on the platform backend decides correctness and awards points.
  A dynamic flag is validated against the **requester's own** running instance, so
  a flag leaked from another user never scores (tested).
- **Answers not leaked**: catalog metadata never contains flags, remediation or
  walkthroughs; those unlock only after a solve (tested).
- **Resource guard + expiry**: `LAB_MAX_PER_USER` caps concurrent labs; a
  background sweeper expires instances past `LAB_TTL` and clears their state.
- **Safe-by-construction targets**: targets that would otherwise need real OS
  interaction are modelled safely — e.g. the command-injection lab runs a
  **simulated shell interpreter over a fake filesystem** and never invokes a real
  shell/subprocess; the path-traversal lab resolves against an **in-memory virtual
  filesystem**, never the host FS. See `docs/SECURITY.md`.

### What production adds (the *infrastructure* half)

- Each `start()` launches a **container** (web labs) or **Firecracker microVM**
  (network/OS/privesc labs) instead of in-process state, with:
  - read-only root FS; no mounted host paths; `--cap-drop=ALL`; no `--privileged`;
    no Docker socket; seccomp/AppArmor profiles;
  - `--network` on a dedicated, egress-blocked bridge; DNS to a sinkhole; cloud
    metadata IP (169.254.169.254) null-routed;
  - `--cpus`, `--memory`, `--pids-limit` quotas;
  - a label with the instance id for routing and reaping.
- A **lab router** maps `labs.<host>/<instance-token>/…` to the instance's private
  address, enforcing the same ownership check at the edge.
- The **orchestrator worker** (Redis queue) handles provision/reset/expire and a
  reaper sweeps overdue instances and orphaned containers.

---

## 4. Request lifecycle (flag capture)

1. User opens a challenge → `GET /api/challenges/<slug>`.
2. User clicks **Start Lab** → `POST /api/challenges/<slug>/lab/start`.
3. Orchestrator authorizes, checks the per-user limit, generates a unique flag,
   provisions an isolated instance, returns its URL/token.
4. User interacts with the target under `/labs/<id>/…` (ownership-checked).
5. User exploits the vulnerability; the target reveals the per-session flag.
6. User submits → `POST /api/challenges/<slug>/submit`.
7. Backend validates (constant-time) against the user's own instance flag,
   records the submission, and on first success awards points idempotently
   (`UNIQUE(user,challenge)` on `solves`), granting achievements.
8. Reset rotates the flag; stop/expiry tears the instance down.

---

## 5. Data model

See `schema.sql`. Aggregates: identity/access (`users`, `sessions`, `tokens`),
catalog (`categories`, `challenges` + version counter, `hints`), live labs
(`lab_instances`), progress/scoring (`submissions`, `solves`, `hint_unlocks`),
learning (`learning_paths`, `learning_path_items`), gamification (`achievements`,
`user_achievements`), competitions (`competitions`, `competition_challenges`,
`teams`, `team_members`, `score_events`), and `audit_logs`. The competition and
team tables are present in the schema and ready for the Phase-5 UI.

---

## 6. Deployment notes

- Set `MYCTF_SECRET_KEY` to a long random value; it signs JWTs and keys flag
  HMACs. Rotating it invalidates existing sessions and static-flag hashes.
- Put the app behind TLS and set the auth cookie `secure=True` (one line in
  `app/auth/routes.py::_set_cookie`).
- Move password hashing to Argon2id (`argon2-cffi`) — the `security.py` interface
  (`hash_password`/`verify_password`) is the only thing to change.
- Run PostgreSQL + Redis; generate Alembic migrations from `schema.sql`.
- Run the orchestrator worker and lab network as a separate, segmented tier.
- A starting-point `Dockerfile` and `docker-compose.yml` are included for the
  app, database and cache; the isolated lab-runner tier is environment-specific
  and intentionally left to your infrastructure (Firecracker/gVisor/K8s).
