"""Data-access layer. The only module (with db.py) that issues SQL.

Functions are grouped by aggregate. They take plain values and return sqlite3.Row
or dicts, never leaking the connection to callers.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from .db import get_db


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ============================================================ users / auth ===
def create_user(username: str, email: str, password_hash: str, role: str = "student",
                display_name: str | None = None, email_verified: bool = False) -> int:
    db = get_db()
    cur = db.execute(
        """INSERT INTO users (username, email, password_hash, role, display_name,
                              email_verified)
           VALUES (?,?,?,?,?,?)""",
        (username, email, password_hash, role, display_name or username,
         1 if email_verified else 0),
    )
    db.commit()
    return cur.lastrowid


def get_user_by_id(user_id: int):
    return get_db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


def get_user_by_username(username: str):
    return get_db().execute(
        "SELECT * FROM users WHERE username=? COLLATE NOCASE", (username,)
    ).fetchone()


def get_user_by_email(email: str):
    return get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()


def get_user_by_login(identifier: str):
    """Allow login by username OR email."""
    return get_db().execute(
        "SELECT * FROM users WHERE username=? COLLATE NOCASE OR email=?",
        (identifier, identifier.lower())
    ).fetchone()


def set_last_login(user_id: int) -> None:
    db = get_db()
    db.execute("UPDATE users SET last_login_at=? WHERE id=?", (_iso(_now()), user_id))
    db.commit()


def set_user_role(user_id: int, role: str) -> None:
    db = get_db()
    db.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    db.commit()


def set_email_verified(user_id: int, verified: bool = True) -> None:
    db = get_db()
    db.execute("UPDATE users SET email_verified=? WHERE id=?",
               (1 if verified else 0, user_id))
    db.commit()


def set_totp_secret(user_id: int, secret: str | None) -> None:
    db = get_db()
    db.execute("UPDATE users SET totp_secret=? WHERE id=?", (secret, user_id))
    db.commit()


def list_users():
    return get_db().execute(
        "SELECT id, username, email, role, email_verified, created_at, last_login_at "
        "FROM users ORDER BY id"
    ).fetchall()


# ---- sessions ----
def create_session(session_id: str, user_id: int, ttl: int,
                   user_agent: str = "", ip: str = "") -> None:
    db = get_db()
    expires = _iso(_now() + timedelta(seconds=ttl))
    db.execute(
        """INSERT INTO sessions (id, user_id, expires_at, user_agent, ip)
           VALUES (?,?,?,?,?)""",
        (session_id, user_id, expires, user_agent, ip),
    )
    db.commit()


def get_session(session_id: str):
    return get_db().execute(
        "SELECT * FROM sessions WHERE id=?", (session_id,)
    ).fetchone()


def session_is_active(session_id: str) -> bool:
    row = get_session(session_id)
    if row is None or row["revoked"]:
        return False
    return row["expires_at"] >= _iso(_now())


def revoke_session(session_id: str) -> None:
    db = get_db()
    db.execute("UPDATE sessions SET revoked=1 WHERE id=?", (session_id,))
    db.commit()


def revoke_user_sessions(user_id: int) -> None:
    """Sign a user out everywhere (used after a password reset)."""
    db = get_db()
    db.execute("UPDATE sessions SET revoked=1 WHERE user_id=?", (user_id,))
    db.commit()


# ---- one-time tokens ----
def create_onetime_token(user_id: int, kind: str, token_hash: str, ttl: int) -> None:
    db = get_db()
    expires = _iso(_now() + timedelta(seconds=ttl))
    db.execute(
        "INSERT INTO tokens (user_id, kind, token_hash, expires_at) VALUES (?,?,?,?)",
        (user_id, kind, token_hash, expires),
    )
    db.commit()


def consume_onetime_token(kind: str, token_hash: str):
    """Return the user_id if a valid unused token matches, else None (and burns it)."""
    db = get_db()
    row = db.execute(
        """SELECT * FROM tokens
           WHERE kind=? AND token_hash=? AND used=0 AND expires_at>=?""",
        (kind, token_hash, _iso(_now())),
    ).fetchone()
    if row is None:
        return None
    db.execute("UPDATE tokens SET used=1 WHERE id=?", (row["id"],))
    db.commit()
    return row["user_id"]


# ======================================================== categories/challenges
def upsert_category(slug: str, name: str, skill: str = "", sort: int = 0) -> int:
    db = get_db()
    existing = db.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()
    if existing:
        db.execute("UPDATE categories SET name=?, skill=?, sort=? WHERE id=?",
                   (name, skill, sort, existing["id"]))
        db.commit()
        return existing["id"]
    cur = db.execute(
        "INSERT INTO categories (slug, name, skill, sort) VALUES (?,?,?,?)",
        (slug, name, skill, sort),
    )
    db.commit()
    return cur.lastrowid


def get_category_by_slug(slug: str):
    return get_db().execute(
        "SELECT * FROM categories WHERE slug=?", (slug,)
    ).fetchone()


def list_categories():
    return get_db().execute("SELECT * FROM categories ORDER BY sort, name").fetchall()


def upsert_challenge(data: dict) -> int:
    """Insert or update a challenge by slug. `data` is validated upstream."""
    db = get_db()
    existing = db.execute(
        "SELECT id, version FROM challenges WHERE slug=?", (data["slug"],)
    ).fetchone()
    fields = dict(
        name=data["name"],
        category_id=data["category_id"],
        difficulty=data["difficulty"],
        points=data["points"],
        est_minutes=data.get("est_minutes"),
        description=data["description"],
        objectives=json.dumps(data.get("objectives", [])),
        lab_kind=data.get("lab_kind", "static"),
        flag_hash=data.get("flag_hash"),
        dynamic_flag=1 if data.get("dynamic_flag") else 0,
        remediation=data.get("remediation"),
        walkthrough=data.get("walkthrough"),
        references_json=json.dumps(data.get("references", [])),
        target_url=data.get("target_url"),
        published=1 if data.get("published", True) else 0,
        sort=data.get("sort", 0),
    )
    if existing:
        sets = ", ".join(f"{k}=?" for k in fields)
        db.execute(
            f"UPDATE challenges SET {sets}, version=version+1 WHERE id=?",
            (*fields.values(), existing["id"]),
        )
        db.commit()
        return existing["id"]
    cols = ", ".join(["slug", *fields])
    ph = ", ".join(["?"] * (len(fields) + 1))
    cur = db.execute(
        f"INSERT INTO challenges ({cols}) VALUES ({ph})",
        (data["slug"], *fields.values()),
    )
    db.commit()
    return cur.lastrowid


def get_challenge(challenge_id: int):
    return get_db().execute(
        "SELECT * FROM challenges WHERE id=?", (challenge_id,)
    ).fetchone()


def get_challenge_by_slug(slug: str, *, include_drafts: bool = True):
    # Neutral public aliases keep implementation/vulnerability names out of
    # player-facing URLs while preserving manifest identity and existing solves.
    if slug.startswith("case-") and slug[5:].isascii() and slug[5:].isdigit() and len(slug) <= 20:
        row = get_db().execute("SELECT * FROM challenges WHERE id=?", (int(slug[5:]),)).fetchone()
    else:
        row = get_db().execute(
            "SELECT * FROM challenges WHERE slug=?", (slug,)
        ).fetchone()
    if row is not None and not include_drafts and not row["published"]:
        return None
    return row


def list_challenges(published_only: bool = True):
    q = ("SELECT c.*, cat.slug AS category_slug, cat.name AS category_name, "
         "cat.skill AS skill FROM challenges c "
         "JOIN categories cat ON cat.id=c.category_id")
    if published_only:
        q += " WHERE c.published=1"
    q += " ORDER BY c.sort, c.points, c.name"
    return get_db().execute(q).fetchall()


def set_challenge_published(challenge_id: int, published: bool) -> None:
    db = get_db()
    db.execute("UPDATE challenges SET published=? WHERE id=?",
               (1 if published else 0, challenge_id))
    db.commit()


# ---- hints ----
def upsert_hint(challenge_id: int, level: int, body: str, cost: int = 0) -> None:
    db = get_db()
    existing = db.execute(
        "SELECT id FROM hints WHERE challenge_id=? AND level=?", (challenge_id, level)
    ).fetchone()
    if existing:
        db.execute("UPDATE hints SET body=?, cost=? WHERE id=?",
                   (body, cost, existing["id"]))
    else:
        db.execute(
            "INSERT INTO hints (challenge_id, level, body, cost) VALUES (?,?,?,?)",
            (challenge_id, level, body, cost),
        )
    db.commit()


def prune_hints(challenge_id: int, keep_levels: list[int]) -> None:
    """Delete hints (and their unlock records) whose level is no longer in the manifest."""
    db = get_db()
    rows = db.execute("SELECT id, level FROM hints WHERE challenge_id=?",
                      (challenge_id,)).fetchall()
    stale = [r["id"] for r in rows if r["level"] not in set(keep_levels)]
    for hid in stale:
        db.execute("DELETE FROM hint_unlocks WHERE hint_id=?", (hid,))
        db.execute("DELETE FROM hints WHERE id=?", (hid,))
    if stale:
        db.commit()


def list_hints(challenge_id: int):
    return get_db().execute(
        "SELECT * FROM hints WHERE challenge_id=? ORDER BY level", (challenge_id,)
    ).fetchall()


def get_hint(hint_id: int):
    return get_db().execute("SELECT * FROM hints WHERE id=?", (hint_id,)).fetchone()


def unlock_hint(user_id: int, hint_id: int, cost: int) -> bool:
    """Idempotent. Returns True if newly unlocked."""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO hint_unlocks (user_id, hint_id, cost_paid) VALUES (?,?,?)",
            (user_id, hint_id, cost),
        )
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def unlocked_hint_ids(user_id: int, challenge_id: int) -> set[int]:
    rows = get_db().execute(
        """SELECT h.id FROM hints h
           JOIN hint_unlocks u ON u.hint_id=h.id AND u.user_id=?
           WHERE h.challenge_id=?""",
        (user_id, challenge_id),
    ).fetchall()
    return {r["id"] for r in rows}


# ============================================================== lab instances ==
def create_lab_instance(instance_id: str, challenge_id: int, user_id: int,
                        flag: str, ttl: int, lab_url: str = "",
                        container_ref: str = "") -> None:
    db = get_db()
    expires = _iso(_now() + timedelta(seconds=ttl))
    db.execute(
        """INSERT INTO lab_instances
             (id, challenge_id, user_id, flag, state, container_ref, lab_url, expires_at)
           VALUES (?,?,?,?,'running',?,?,?)""",
        (instance_id, challenge_id, user_id, flag, container_ref, lab_url, expires),
    )
    db.commit()


def get_lab_instance(instance_id: str):
    return get_db().execute(
        "SELECT * FROM lab_instances WHERE id=?", (instance_id,)
    ).fetchone()


def get_user_lab(user_id: int, challenge_id: int):
    return get_db().execute(
        "SELECT * FROM lab_instances WHERE user_id=? AND challenge_id=?",
        (user_id, challenge_id),
    ).fetchone()


def count_running_labs(user_id: int) -> int:
    row = get_db().execute(
        "SELECT COUNT(*) AS n FROM lab_instances WHERE user_id=? AND state='running'",
        (user_id,),
    ).fetchone()
    return row["n"]


def set_lab_state(instance_id: str, state: str) -> None:
    db = get_db()
    db.execute("UPDATE lab_instances SET state=? WHERE id=?", (state, instance_id))
    db.commit()


def delete_lab_instance(instance_id: str) -> None:
    db = get_db()
    db.execute("DELETE FROM lab_instances WHERE id=?", (instance_id,))
    db.commit()


def expired_lab_instances():
    return get_db().execute(
        "SELECT * FROM lab_instances WHERE expires_at < ? AND state='running'",
        (_iso(_now()),),
    ).fetchall()


def user_running_lab_ids(user_id: int) -> set[int]:
    """Challenge ids that have a running lab for this user (catalog status)."""
    rows = get_db().execute(
        "SELECT challenge_id FROM lab_instances WHERE user_id=? AND state='running'",
        (user_id,),
    ).fetchall()
    return {r["challenge_id"] for r in rows}


def list_running_labs():
    return get_db().execute(
        """SELECT l.*, u.username, c.name AS challenge_name
           FROM lab_instances l
           JOIN users u ON u.id=l.user_id
           JOIN challenges c ON c.id=l.challenge_id
           WHERE l.state='running' ORDER BY l.created_at DESC"""
    ).fetchall()


# ============================================================ submissions/solves
def record_submission(user_id: int, challenge_id: int, flag: str, correct: bool) -> None:
    db = get_db()
    db.execute(
        """INSERT INTO submissions (user_id, challenge_id, submitted_flag, correct)
           VALUES (?,?,?,?)""",
        (user_id, challenge_id, flag, 1 if correct else 0),
    )
    db.commit()


def has_solved(user_id: int, challenge_id: int) -> bool:
    return get_db().execute(
        "SELECT 1 FROM solves WHERE user_id=? AND challenge_id=?",
        (user_id, challenge_id),
    ).fetchone() is not None


def record_solve(user_id: int, challenge_id: int, points: int) -> Optional[dict]:
    """Idempotent award. Returns {points, first_blood} on a NEW solve, else None."""
    db = get_db()
    first_blood = db.execute(
        "SELECT 1 FROM solves WHERE challenge_id=?", (challenge_id,)
    ).fetchone() is None
    try:
        db.execute(
            """INSERT INTO solves (user_id, challenge_id, points_awarded, first_blood)
               VALUES (?,?,?,?)""",
            (user_id, challenge_id, points, 1 if first_blood else 0),
        )
        db.commit()
    except Exception:
        db.rollback()
        return None  # already solved -> no double award
    return {"points": points, "first_blood": first_blood}


def count_attempts(user_id: int, challenge_id: int) -> int:
    row = get_db().execute(
        "SELECT COUNT(*) AS n FROM submissions WHERE user_id=? AND challenge_id=?",
        (user_id, challenge_id),
    ).fetchone()
    return row["n"]


def user_solved_ids(user_id: int) -> set[int]:
    rows = get_db().execute(
        "SELECT challenge_id FROM solves WHERE user_id=?", (user_id,)
    ).fetchall()
    return {r["challenge_id"] for r in rows}


def user_score(user_id: int) -> int:
    row = get_db().execute(
        """SELECT COALESCE(SUM(points_awarded),0) AS pts FROM solves WHERE user_id=?""",
        (user_id,),
    ).fetchone()
    spent = get_db().execute(
        "SELECT COALESCE(SUM(cost_paid),0) AS c FROM hint_unlocks WHERE user_id=?",
        (user_id,),
    ).fetchone()
    return int(row["pts"]) - int(spent["c"])


def user_solve_rows(user_id: int):
    return get_db().execute(
        """SELECT s.*, c.name, c.slug, c.difficulty, cat.skill
           FROM solves s JOIN challenges c ON c.id=s.challenge_id
           JOIN categories cat ON cat.id=c.category_id
           WHERE s.user_id=? ORDER BY s.created_at DESC""",
        (user_id,),
    ).fetchall()


def current_streak(user_id: int) -> int:
    """Consecutive-day solve streak ending today/yesterday (read-only, display)."""
    rows = get_db().execute(
        "SELECT DISTINCT date(created_at) AS d FROM solves WHERE user_id=? "
        "ORDER BY d DESC", (user_id,),
    ).fetchall()
    if not rows:
        return 0
    from datetime import date, datetime, timedelta
    days = [datetime.strptime(r["d"], "%Y-%m-%d").date() for r in rows]
    today = _now().date()
    if days[0] not in (today, today - timedelta(days=1)):
        return 0
    streak, prev = 1, days[0]
    for d in days[1:]:
        if d == prev - timedelta(days=1):
            streak += 1
            prev = d
        else:
            break
    return streak


def recent_submissions(user_id: int, limit: int = 8):
    return get_db().execute(
        """SELECT su.*, c.name, c.slug FROM submissions su
           JOIN challenges c ON c.id=su.challenge_id
           WHERE su.user_id=? ORDER BY su.created_at DESC LIMIT ?""",
        (user_id, limit),
    ).fetchall()


# ---- leaderboard ----
def leaderboard(limit: int = 100):
    return get_db().execute(
        """SELECT u.id, u.username, u.display_name,
                  COALESCE(SUM(s.points_awarded),0) -
                  COALESCE((SELECT SUM(cost_paid) FROM hint_unlocks WHERE user_id=u.id),0)
                    AS score,
                  COUNT(s.id) AS solves,
                  MAX(s.created_at) AS last_solve
           FROM users u
           LEFT JOIN solves s ON s.user_id=u.id
           WHERE u.role != 'administrator'
           GROUP BY u.id
           HAVING solves > 0
           ORDER BY score DESC, last_solve ASC
           LIMIT ?""",
        (limit,),
    ).fetchall()


def leaderboard_extras(user_ids: list[int]) -> dict[int, dict]:
    """First-blood counts per user (read-only, for the scoreboard)."""
    if not user_ids:
        return {}
    marks = ",".join("?" * len(user_ids))
    rows = get_db().execute(
        f"SELECT user_id, SUM(first_blood) AS fb FROM solves WHERE user_id IN ({marks}) "
        "GROUP BY user_id", user_ids,
    ).fetchall()
    return {r["user_id"]: {"first_bloods": int(r["fb"] or 0)} for r in rows}


def score_timeline(user_ids: list[int]) -> dict[int, list[dict]]:
    """Point-changing events per user, oldest first: solves (+) and paid hints (-)."""
    if not user_ids:
        return {}
    marks = ",".join("?" * len(user_ids))
    db = get_db()
    rows = db.execute(
        f"""SELECT user_id, created_at AS at, points_awarded AS delta FROM solves
            WHERE user_id IN ({marks})
            UNION ALL
            SELECT user_id, created_at AS at, -cost_paid AS delta FROM hint_unlocks
            WHERE user_id IN ({marks}) AND cost_paid > 0
            ORDER BY at""", [*user_ids, *user_ids],
    ).fetchall()
    out: dict[int, list[dict]] = {uid: [] for uid in user_ids}
    for r in rows:
        out[r["user_id"]].append({"at": r["at"], "delta": int(r["delta"])})
    return out


def recent_solves_feed(limit: int = 12):
    """Latest solves across the platform (non-admin players), newest first."""
    return get_db().execute(
        """SELECT s.created_at, s.points_awarded, s.first_blood, s.challenge_id, s.user_id,
                  c.name AS challenge, u.username, u.display_name
           FROM solves s JOIN users u ON u.id=s.user_id
           JOIN challenges c ON c.id=s.challenge_id
           WHERE u.role != 'administrator' AND c.published=1
           ORDER BY s.created_at DESC, s.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()


def daily_solve_counts(user_id: int, days: int = 112) -> dict[str, int]:
    """Solves per UTC day over the last `days` days (for the activity heatmap)."""
    rows = get_db().execute(
        """SELECT date(created_at) AS d, COUNT(*) AS n FROM solves
           WHERE user_id=? AND created_at >= datetime('now', ?)
           GROUP BY d""",
        (user_id, f"-{int(days)} days"),
    ).fetchall()
    return {r["d"]: int(r["n"]) for r in rows}


def user_first_bloods(user_id: int) -> int:
    row = get_db().execute(
        "SELECT COALESCE(SUM(first_blood),0) AS n FROM solves WHERE user_id=?", (user_id,)
    ).fetchone()
    return int(row["n"])


def user_rank(user_id: int) -> int:
    rows = leaderboard(100000)
    for i, r in enumerate(rows, start=1):
        if r["id"] == user_id:
            return i
    return 0


def skill_breakdown(user_id: int) -> dict[str, dict]:
    """Per-skill solved vs available points, for the dashboard radar."""
    rows = get_db().execute(
        """SELECT cat.skill AS skill,
                  SUM(CASE WHEN s.id IS NOT NULL THEN c.points ELSE 0 END) AS earned,
                  SUM(c.points) AS available,
                  COUNT(c.id) AS total,
                  COUNT(s.id) AS solved
           FROM challenges c
           JOIN categories cat ON cat.id=c.category_id
           LEFT JOIN solves s ON s.challenge_id=c.id AND s.user_id=?
           WHERE c.published=1
           GROUP BY cat.skill""",
        (user_id,),
    ).fetchall()
    out = {}
    for r in rows:
        out[r["skill"] or "Other"] = {
            "earned": int(r["earned"] or 0),
            "available": int(r["available"] or 0),
            "solved": int(r["solved"] or 0),
            "total": int(r["total"] or 0),
        }
    return out


# ============================================================ learning paths ===
def upsert_learning_path(slug, name, level, description, sort=0) -> int:
    db = get_db()
    existing = db.execute(
        "SELECT id FROM learning_paths WHERE slug=?", (slug,)
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE learning_paths SET name=?, level=?, description=?, sort=? WHERE id=?",
            (name, level, description, sort, existing["id"]),
        )
        db.commit()
        return existing["id"]
    cur = db.execute(
        "INSERT INTO learning_paths (slug, name, level, description, sort) "
        "VALUES (?,?,?,?,?)",
        (slug, name, level, description, sort),
    )
    db.commit()
    return cur.lastrowid


def set_path_item(path_id: int, challenge_id: int, sort: int = 0) -> None:
    db = get_db()
    try:
        db.execute(
            "INSERT INTO learning_path_items (path_id, challenge_id, sort) VALUES (?,?,?)",
            (path_id, challenge_id, sort),
        )
        db.commit()
    except Exception:
        db.rollback()


def list_learning_paths():
    return get_db().execute(
        "SELECT * FROM learning_paths ORDER BY sort, name"
    ).fetchall()


def path_items(path_id: int):
    return get_db().execute(
        """SELECT c.*, i.sort AS item_sort FROM learning_path_items i
           JOIN challenges c ON c.id=i.challenge_id
           WHERE i.path_id=? ORDER BY i.sort""",
        (path_id,),
    ).fetchall()


# ============================================================== achievements ===
def upsert_achievement(slug, name, description, icon="award") -> int:
    db = get_db()
    existing = db.execute(
        "SELECT id FROM achievements WHERE slug=?", (slug,)
    ).fetchone()
    if existing:
        db.execute("UPDATE achievements SET name=?, description=?, icon=? WHERE id=?",
                   (name, description, icon, existing["id"]))
        db.commit()
        return existing["id"]
    cur = db.execute(
        "INSERT INTO achievements (slug, name, description, icon) VALUES (?,?,?,?)",
        (slug, name, description, icon),
    )
    db.commit()
    return cur.lastrowid


def grant_achievement(user_id: int, slug: str) -> bool:
    db = get_db()
    ach = db.execute("SELECT id FROM achievements WHERE slug=?", (slug,)).fetchone()
    if not ach:
        return False
    try:
        db.execute(
            "INSERT INTO user_achievements (user_id, achievement_id) VALUES (?,?)",
            (user_id, ach["id"]),
        )
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def user_achievements(user_id: int):
    return get_db().execute(
        """SELECT a.* FROM achievements a
           JOIN user_achievements ua ON ua.achievement_id=a.id
           WHERE ua.user_id=? ORDER BY ua.created_at DESC""",
        (user_id,),
    ).fetchall()


# ================================================================ audit log ===
def audit(user_id: Optional[int], action: str, detail: str = "", ip: str = "") -> None:
    db = get_db()
    db.execute(
        "INSERT INTO audit_logs (user_id, action, detail, ip) VALUES (?,?,?,?)",
        (user_id, action, detail, ip),
    )
    db.commit()


def recent_audit(limit: int = 100):
    return get_db().execute(
        """SELECT al.*, u.username FROM audit_logs al
           LEFT JOIN users u ON u.id=al.user_id
           ORDER BY al.created_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()


# ============================================================ global counters ==
def platform_stats() -> dict:
    db = get_db()
    users = db.execute(
        "SELECT COUNT(*) AS n FROM users WHERE role!='administrator'"
    ).fetchone()["n"]
    chals = db.execute("SELECT COUNT(*) AS n FROM challenges WHERE published=1").fetchone()["n"]
    solves = db.execute("SELECT COUNT(*) AS n FROM solves").fetchone()["n"]
    labs = db.execute(
        "SELECT COUNT(*) AS n FROM lab_instances WHERE state='running'"
    ).fetchone()["n"]
    return {"users": users, "challenges": chals, "solves": solves, "running_labs": labs}


# ============================================================ profile photos ==
def get_avatar(user_id: int):
    return get_db().execute(
        "SELECT mime, data, updated_at FROM user_avatars WHERE user_id=?", (user_id,)
    ).fetchone()


def set_avatar(user_id: int, mime: str, data: bytes) -> None:
    db = get_db()
    db.execute(
        """INSERT INTO user_avatars (user_id, mime, data, updated_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(user_id) DO UPDATE SET mime=excluded.mime, data=excluded.data,
                                              updated_at=excluded.updated_at""",
        (user_id, mime, data),
    )
    db.commit()


def delete_avatar(user_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM user_avatars WHERE user_id=?", (user_id,))
    db.commit()


def avatar_urls(user_ids) -> dict[int, str]:
    """user id -> versioned photo URL, for users who uploaded one."""
    ids = list({int(i) for i in user_ids})
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    rows = get_db().execute(
        f"SELECT user_id, updated_at FROM user_avatars WHERE user_id IN ({marks})", ids
    ).fetchall()
    return {r["user_id"]: f"/api/avatars/{r['user_id']}?v="
            + "".join(ch for ch in r["updated_at"] if ch.isdigit()) for r in rows}
