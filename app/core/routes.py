"""Core platform: dashboard, catalog, challenge play, labs control, flag submit,
hints, leaderboard, learning paths, achievements, profile, docs.

Answer material (flags, walkthroughs, remediation) is never exposed through
ordinary catalog metadata. Walkthrough/remediation unlock only after a solve.
"""
from __future__ import annotations

import json

from flask import (Blueprint, abort, current_app, jsonify, redirect,
                   render_template, request, url_for)

from .. import labs, limiter, models
from ..auth import current_user, login_required
from ..scoring import check_submission

bp = Blueprint("core", __name__)


def _playable_challenge(slug: str, user):
    """Look up a challenge a user may interact with. Drafts (unpublished) are
    visible to administrators only, so nobody can start labs, submit flags or
    unlock hints for content that hasn't been released."""
    challenge = models.get_challenge_by_slug(
        slug, include_drafts=(user["role"] == "administrator"))
    if not challenge:
        abort(404)
    return challenge


# =============================================================== serializers ==
def serialize_challenge(challenge, user, *, detail: bool = False) -> dict:
    solved_ids = models.user_solved_ids(user["id"]) if user else set()
    is_solved = challenge["id"] in solved_ids
    out = {
        "id": challenge["id"],
        "slug": challenge["slug"],
        "name": challenge["name"],
        "category": challenge["category_slug"] if "category_slug" in challenge.keys()
                    else None,
        "category_name": challenge["category_name"] if "category_name" in challenge.keys()
                         else None,
        "skill": challenge["skill"] if "skill" in challenge.keys() else None,
        "difficulty": challenge["difficulty"],
        "points": challenge["points"],
        "est_minutes": challenge["est_minutes"],
        "has_lab": labs.registry.is_live_lab(challenge["lab_kind"]),
        "lab_kind": challenge["lab_kind"],
        "is_shell": labs.registry.is_shell_lab(challenge["lab_kind"]),
        "solved": is_solved,
    }
    if detail:
        out["description"] = challenge["description"]
        out["objectives"] = json.loads(challenge["objectives"] or "[]")
        out["references"] = json.loads(challenge["references_json"] or "[]")
        out["target_url"] = challenge["target_url"]
        out["attempts"] = models.count_attempts(user["id"], challenge["id"]) if user else 0
        out["hints"] = _serialize_hints(challenge, user)
        # Post-solve only — never leak the solution through metadata.
        if is_solved:
            out["remediation"] = challenge["remediation"]
            out["walkthrough"] = challenge["walkthrough"]
        if user:
            inst = models.get_user_lab(user["id"], challenge["id"])
            out["lab"] = ({"instance_id": inst["id"], "url": inst["lab_url"],
                           "state": inst["state"], "expires_at": inst["expires_at"]}
                          if inst else None)
    return out


def _serialize_hints(challenge, user) -> list[dict]:
    unlocked = models.unlocked_hint_ids(user["id"], challenge["id"]) if user else set()
    out = []
    for h in models.list_hints(challenge["id"]):
        is_unlocked = h["id"] in unlocked
        out.append({"id": h["id"], "level": h["level"], "cost": h["cost"],
                    "unlocked": is_unlocked,
                    "body": h["body"] if is_unlocked else None})
    return out


# ================================================================ HTML pages ==
@bp.get("/")
def index():
    if current_user():
        return redirect(url_for("core.dashboard"))
    return render_template("landing.html", stats=models.platform_stats())


@bp.get("/dashboard")
@login_required
def dashboard():
    user = current_user()
    return render_template("dashboard.html", **_dashboard_data(user))


@bp.get("/challenges")
@login_required
def challenges_page():
    user = current_user()
    rows = models.list_challenges()
    running = models.user_running_lab_ids(user["id"])
    chals = []
    for c in rows:
        data = serialize_challenge(c, user)
        data["status"] = ("solved" if data["solved"]
                          else "progress" if c["id"] in running else "new")
        chals.append(data)
    cats = models.list_categories()
    return render_template("challenges.html", challenges=chals, categories=cats)


@bp.get("/challenges/<slug>")
@login_required
def challenge_page(slug):
    user = current_user()
    challenge = models.get_challenge_by_slug(slug)
    if not challenge or not challenge["published"]:
        abort(404)
    full = models.list_challenges()
    joined = next((c for c in full if c["slug"] == slug), challenge)
    data = serialize_challenge(joined, user, detail=True)
    return render_template("challenge.html", c=data)


@bp.get("/leaderboard")
@login_required
def leaderboard_page():
    user = current_user()
    return render_template("leaderboard.html",
                           rows=models.leaderboard(100),
                           me=user["id"])


@bp.get("/paths")
@login_required
def paths_page():
    user = current_user()
    solved = models.user_solved_ids(user["id"])
    paths = []
    for p in models.list_learning_paths():
        items = models.path_items(p["id"])
        done = sum(1 for it in items if it["id"] in solved)
        paths.append({"path": p, "items": items, "done": done, "total": len(items)})
    return render_template("paths.html", paths=paths, solved=solved)


@bp.get("/achievements")
@login_required
def achievements_page():
    user = current_user()
    earned = {a["slug"] for a in models.user_achievements(user["id"])}
    allach = models.get_db().execute(
        "SELECT * FROM achievements ORDER BY id").fetchall()
    return render_template("achievements.html", achievements=allach, earned=earned)


@bp.get("/profile")
@login_required
def profile_page():
    user = current_user()
    return render_template("profile.html",
                           user=user,
                           solves=models.user_solve_rows(user["id"]),
                           score=models.user_score(user["id"]),
                           rank=models.user_rank(user["id"]),
                           skills=models.skill_breakdown(user["id"]),
                           achievements=models.user_achievements(user["id"]))


@bp.get("/docs")
def docs_page():
    return render_template("docs.html", live_kinds=labs.registry.live_kinds())


# ==================================================================== JSON API ==
@bp.get("/api/dashboard")
@login_required
def api_dashboard():
    user = current_user()
    data = _dashboard_data(user)
    # make JSON-safe
    data["recent"] = [dict(r) for r in data["recent"]]
    data["achievements"] = [dict(a) for a in data["achievements"]]
    data["recommended"] = (serialize_challenge(data["recommended"], user)
                           if data["recommended"] is not None else None)
    data["in_progress"] = (serialize_challenge(data["in_progress"], user)
                           if data["in_progress"] is not None else None)
    data.pop("user", None)
    return jsonify(data)


@bp.get("/api/challenges")
@login_required
def api_challenges():
    user = current_user()
    running = models.user_running_lab_ids(user["id"])
    out = []
    for c in models.list_challenges():
        data = serialize_challenge(c, user)
        data["status"] = ("solved" if data["solved"]
                          else "progress" if c["id"] in running else "new")
        out.append(data)
    return jsonify(out)


@bp.get("/api/challenges/<slug>")
@login_required
def api_challenge(slug):
    user = current_user()
    # Admins can open drafts so they can test a challenge before publishing it.
    rows = models.list_challenges(published_only=user["role"] != "administrator")
    c = next((r for r in rows if r["slug"] == slug), None)
    if c is None:
        abort(404)
    return jsonify(serialize_challenge(c, user, detail=True))


@bp.post("/api/challenges/<slug>/lab/start")
@login_required
def api_lab_start(slug):
    user = current_user()
    challenge = _playable_challenge(slug, user)
    try:
        inst = labs.start(user["id"], challenge)
    except labs.LabError as e:
        return jsonify({"error": e.message}), e.status
    return jsonify({"ok": True, "instance_id": inst["id"], "url": inst["lab_url"],
                    "expires_at": inst["expires_at"]})


@bp.post("/api/labs/<instance_id>/stop")
@login_required
def api_lab_stop(instance_id):
    user = current_user()
    try:
        labs.stop(user["id"], instance_id)
    except labs.LabError as e:
        return jsonify({"error": e.message}), e.status
    return jsonify({"ok": True})


@bp.post("/api/labs/<instance_id>/reset")
@login_required
def api_lab_reset(instance_id):
    user = current_user()
    try:
        inst = labs.reset(user["id"], instance_id)
    except labs.LabError as e:
        return jsonify({"error": e.message}), e.status
    return jsonify({"ok": True, "instance_id": inst["id"], "url": inst["lab_url"],
                    "expires_at": inst["expires_at"]})


@bp.post("/api/challenges/<slug>/submit")
@login_required
def api_submit(slug):
    user = current_user()
    challenge = _playable_challenge(slug, user)
    key = f"flag:{user['id']}"
    if not limiter.allow(key, current_app.config["RATE_LIMIT_FLAG_SUBMITS"],
                         current_app.config["RATE_LIMIT_WINDOW"]):
        return jsonify({"error": "Too many submissions, slow down."}), 429
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = request.form.to_dict()
    submitted = data.get("flag", "")
    if not isinstance(submitted, str) or len(submitted) > 256:
        return jsonify({"error": "Flag must be text of at most 256 characters."}), 400
    result = check_submission(user["id"], challenge, submitted)
    status = 200 if result["correct"] else 400
    return jsonify(result), status


@bp.post("/api/challenges/<slug>/hints/<int:level>")
@login_required
def api_unlock_hint(slug, level):
    user = current_user()
    challenge = _playable_challenge(slug, user)
    hint = next((h for h in models.list_hints(challenge["id"]) if h["level"] == level),
                None)
    if hint is None:
        abort(404)
    models.unlock_hint(user["id"], hint["id"], hint["cost"])
    models.audit(user["id"], "hint_unlock", f"challenge={slug} level={level}")
    return jsonify({"ok": True, "level": level, "cost": hint["cost"],
                    "body": hint["body"]})


@bp.get("/api/leaderboard")
@login_required
def api_leaderboard():
    rows = models.leaderboard(100)
    return jsonify([{"rank": i, "username": r["username"],
                     "display_name": r["display_name"] or r["username"],
                     "score": r["score"], "solves": r["solves"]}
                    for i, r in enumerate(rows, 1)])


@bp.get("/api/public")
def api_public():
    """Unauthenticated: landing-page counters and the docs page's lab list."""
    stats = models.platform_stats()
    return jsonify({
        "stats": {"users": stats["users"], "challenges": stats["challenges"],
                  "solves": stats["solves"],
                  "categories": len(models.list_categories())},
        "live_kinds": labs.registry.live_kinds(),
    })


@bp.get("/api/profile")
@login_required
def api_profile():
    from ..auth.routes import _public_user
    user = current_user()
    return jsonify({
        "user": _public_user(user),
        "score": models.user_score(user["id"]),
        "rank": models.user_rank(user["id"]) or None,
        "solves": [{"name": r["name"], "slug": r["slug"],
                    "difficulty": r["difficulty"], "skill": r["skill"],
                    "points_awarded": r["points_awarded"],
                    "created_at": r["created_at"]}
                   for r in models.user_solve_rows(user["id"])],
        "skills": models.skill_breakdown(user["id"]),
        "achievements": [_serialize_achievement(a, earned=True)
                         for a in models.user_achievements(user["id"])],
    })


@bp.get("/api/paths")
@login_required
def api_paths():
    solved = models.user_solved_ids(current_user()["id"])
    out = []
    for p in models.list_learning_paths():
        items = [it for it in models.path_items(p["id"]) if it["published"]]
        out.append({
            "slug": p["slug"], "name": p["name"], "level": p["level"],
            "description": p["description"],
            "done": sum(1 for it in items if it["id"] in solved),
            "total": len(items),
            "items": [{"slug": it["slug"], "name": it["name"],
                       "difficulty": it["difficulty"], "points": it["points"],
                       "solved": it["id"] in solved} for it in items],
        })
    return jsonify(out)


@bp.get("/api/achievements")
@login_required
def api_achievements():
    earned = {a["slug"] for a in models.user_achievements(current_user()["id"])}
    rows = models.get_db().execute("SELECT * FROM achievements ORDER BY id").fetchall()
    return jsonify([_serialize_achievement(a, earned=a["slug"] in earned) for a in rows])


# ================================================================= internals ==
def _serialize_achievement(row, *, earned: bool) -> dict:
    return {"slug": row["slug"], "name": row["name"],
            "description": row["description"], "earned": earned}



def _dashboard_data(user) -> dict:
    solved_ids = models.user_solved_ids(user["id"])
    all_chals = models.list_challenges()
    total = len(all_chals)
    completed = len(solved_ids)
    recommended = next((c for c in all_chals if c["id"] not in solved_ids), None)
    # "Continue where you left off": a challenge with a running lab, else the
    # most recently attempted-but-unsolved challenge. Read-only presentation.
    running = models.user_running_lab_ids(user["id"])
    in_progress = next((c for c in all_chals if c["id"] in running), None)
    if in_progress is None:
        for sub in models.recent_submissions(user["id"], 20):
            if sub["challenge_id"] not in solved_ids:
                in_progress = next((c for c in all_chals
                                    if c["id"] == sub["challenge_id"]), None)
                if in_progress:
                    break
    return {
        "user": user,
        "score": models.user_score(user["id"]),
        "rank": models.user_rank(user["id"]),
        "streak": models.current_streak(user["id"]),
        "completed": completed,
        "total": total,
        "available": total - completed,
        "completion_pct": round(100 * completed / total, 1) if total else 0.0,
        "skills": models.skill_breakdown(user["id"]),
        "recent": models.recent_submissions(user["id"], 8),
        "recommended": recommended,
        "in_progress": in_progress,
        "achievements": models.user_achievements(user["id"])[:6],
        "stats": models.platform_stats(),
    }
