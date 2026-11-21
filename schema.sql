-- MyCTF database schema (SQLite dev implementation).
-- The production target is PostgreSQL; types are kept portable and the
-- data-access layer (app/models.py) is the only code that touches SQL,
-- so swapping the driver is localized. See docs/ARCHITECTURE.md.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Identity & access
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    NOT NULL UNIQUE,
    email           TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'student'
                        CHECK (role IN ('student', 'instructor', 'administrator')),
    email_verified  INTEGER NOT NULL DEFAULT 0,
    totp_secret     TEXT,                      -- NULL = 2FA disabled
    display_name    TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Email sign-in codes: one active code per user, stored hashed, with an attempt counter.
CREATE TABLE IF NOT EXISTS login_codes (
    user_id         INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    code_hash       TEXT    NOT NULL,
    expires_at      TEXT    NOT NULL,
    attempts        INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Optional profile photo, validated and stripped of metadata on upload (app/images.py).
CREATE TABLE IF NOT EXISTS user_avatars (
    user_id         INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    mime            TEXT    NOT NULL CHECK (mime IN ('image/png', 'image/jpeg')),
    data            BLOB    NOT NULL,
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Server-side sessions so tokens can be revoked (logout / forced expiry).
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT    PRIMARY KEY,           -- random token id (jti)
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT    NOT NULL,
    revoked     INTEGER NOT NULL DEFAULT 0,
    user_agent  TEXT,
    ip          TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- One-time tokens for email verification and password reset.
CREATE TABLE IF NOT EXISTS tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind        TEXT    NOT NULL CHECK (kind IN ('verify_email', 'reset_password')),
    token_hash  TEXT    NOT NULL,              -- store hash, never the raw token
    expires_at  TEXT    NOT NULL,
    used        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tokens_user ON tokens(user_id, kind);

-- ---------------------------------------------------------------------------
-- Catalog
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    slug    TEXT    NOT NULL UNIQUE,
    name    TEXT    NOT NULL,
    skill   TEXT,                              -- maps to the dashboard skill breakdown
    sort    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS challenges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    difficulty      TEXT    NOT NULL
                        CHECK (difficulty IN ('very_easy','easy','medium','hard','insane')),
    points          INTEGER NOT NULL,
    est_minutes     INTEGER,
    description     TEXT    NOT NULL,
    objectives      TEXT,                      -- JSON array
    -- lab_kind names a handler in app/labs/registry.py. 'static' = no live lab.
    lab_kind        TEXT    NOT NULL DEFAULT 'static',
    -- Static flag (hashed) for challenges whose flag is not per-session.
    -- Per-session labs generate dynamic flags and ignore this column.
    flag_hash       TEXT,
    dynamic_flag    INTEGER NOT NULL DEFAULT 0,
    remediation     TEXT,
    walkthrough     TEXT,
    references_json TEXT,                      -- JSON array of {title,url}
    target_url      TEXT,                      -- optional external target (http/https)
    version         INTEGER NOT NULL DEFAULT 1,
    published       INTEGER NOT NULL DEFAULT 1,
    sort            INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_challenges_cat ON challenges(category_id);
CREATE INDEX IF NOT EXISTS idx_challenges_pub ON challenges(published);

CREATE TABLE IF NOT EXISTS hints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge_id    INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    level           INTEGER NOT NULL,          -- 1,2,3
    body            TEXT    NOT NULL,
    cost            INTEGER NOT NULL DEFAULT 0,
    UNIQUE (challenge_id, level)
);

-- ---------------------------------------------------------------------------
-- Live labs
-- ---------------------------------------------------------------------------
-- A lab instance is a per-user runtime for a challenge. In this dev build the
-- "instance" is in-process state keyed by this row; in production the
-- orchestrator would attach a container/microVM id and a routable URL.
CREATE TABLE IF NOT EXISTS lab_instances (
    id              TEXT    PRIMARY KEY,       -- random id, also used in lab URLs
    challenge_id    INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    flag            TEXT    NOT NULL,          -- the per-session flag for THIS instance
    state           TEXT    NOT NULL DEFAULT 'running'
                        CHECK (state IN ('starting','running','stopped','expired')),
    container_ref   TEXT,                      -- production: container/microVM id
    lab_url         TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    expires_at      TEXT    NOT NULL,
    UNIQUE (challenge_id, user_id)             -- one live instance per user/challenge
);
CREATE INDEX IF NOT EXISTS idx_labs_user ON lab_instances(user_id);
CREATE INDEX IF NOT EXISTS idx_labs_expiry ON lab_instances(expires_at);

-- ---------------------------------------------------------------------------
-- Progress & scoring
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS submissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id    INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    submitted_flag  TEXT    NOT NULL,
    correct         INTEGER NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_sub_chal ON submissions(challenge_id);

-- A solve is the authoritative "this user completed this challenge" record.
-- UNIQUE(user,challenge) is what makes scoring idempotent (award once).
CREATE TABLE IF NOT EXISTS solves (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id    INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    points_awarded  INTEGER NOT NULL,
    first_blood     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, challenge_id)
);
CREATE INDEX IF NOT EXISTS idx_solves_user ON solves(user_id);

CREATE TABLE IF NOT EXISTS hint_unlocks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hint_id         INTEGER NOT NULL REFERENCES hints(id) ON DELETE CASCADE,
    cost_paid       INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, hint_id)
);

-- ---------------------------------------------------------------------------
-- Learning paths
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS learning_paths (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    level       TEXT    NOT NULL,
    description TEXT,
    sort        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS learning_path_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path_id         INTEGER NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    challenge_id    INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    sort            INTEGER NOT NULL DEFAULT 0,
    UNIQUE (path_id, challenge_id)
);

-- ---------------------------------------------------------------------------
-- Gamification
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS achievements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    description TEXT,
    icon        TEXT
);

CREATE TABLE IF NOT EXISTS user_achievements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id  INTEGER NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, achievement_id)
);

-- ---------------------------------------------------------------------------
-- Competitions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS competitions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    description TEXT,
    starts_at   TEXT,
    ends_at     TEXT,
    freeze_at   TEXT,
    mode        TEXT    NOT NULL DEFAULT 'individual'
                    CHECK (mode IN ('individual','team')),
    published   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS competition_challenges (
    competition_id  INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    challenge_id    INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    PRIMARY KEY (competition_id, challenge_id)
);

CREATE TABLE IF NOT EXISTS teams (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id  INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    name            TEXT    NOT NULL,
    captain_id      INTEGER NOT NULL REFERENCES users(id),
    UNIQUE (competition_id, name)
);

CREATE TABLE IF NOT EXISTS team_members (
    team_id     INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (team_id, user_id)
);

-- Competition-scoped score events (kept separate from the global solves table
-- so an event can have its own scoring / freeze without touching global rank).
CREATE TABLE IF NOT EXISTS score_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id  INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id    INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    points          INTEGER NOT NULL,
    first_blood     INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (competition_id, user_id, challenge_id)
);

-- ---------------------------------------------------------------------------
-- Audit
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action      TEXT    NOT NULL,
    detail      TEXT,
    ip          TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
