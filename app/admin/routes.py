"""Administrator panel: challenge publishing, user management, lab monitoring,
submission review, analytics and audit logs. All endpoints require the
administrator role.
"""
from __future__ import annotations

from flask import (Blueprint, abort, jsonify, redirect, render_template,
                   request, url_for)

from .. import labs, models
from ..auth import admin_required, current_user
from ..manifest import ManifestError, validate

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


# ----------------------------------------------------------------- HTML pages
@bp.get("/")
@admin_required
def home():
    return render_template("admin/home.html",
                           stats=models.platform_stats(),
                           users=models.list_users(),
                           running=models.list_running_labs(),
                           audit=models.recent_audit(40))


@bp.get("/challenges")
@admin_required
def challenges():
    return render_template("admin/challenges.html",
                           challenges=models.list_challenges(published_only=False),
                           categories=models.list_categories())


# --------------------------------------------------------------------- JSON API
@bp.get("/api/overview")
@admin_required
def overview():
    return jsonify({
        "stats": models.platform_stats(),
        "users": [{"id": u["id"], "username": u["username"], "email": u["email"],
                   "role": u["role"], "email_verified": bool(u["email_verified"]),
                   "created_at": u["created_at"], "last_login_at": u["last_login_at"]}
                  for u in models.list_users()],
    })


@bp.get("/api/challenges")
@admin_required
def list_all_challenges():
    return jsonify([{"id": c["id"], "slug": c["slug"], "name": c["name"],
                     "category_name": c["category_name"],
                     "difficulty": c["difficulty"], "lab_kind": c["lab_kind"],
                     "points": c["points"], "published": bool(c["published"])}
                    for c in models.list_challenges(published_only=False)])


@bp.get("/api/categories")
@admin_required
def list_categories():
    return jsonify([{"slug": c["slug"], "name": c["name"]}
                    for c in models.list_categories()])


@bp.post("/api/challenges/validate")
@admin_required
def validate_manifest():
    """Validate a manifest without publishing — the pre-publish safety gate."""
    data = _json_body()
    try:
        norm = validate(data)
    except ManifestError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "normalized": {k: norm[k] for k in
                    ("slug", "name", "category", "difficulty", "points",
                     "lab_kind", "dynamic_flag", "published")}})


@bp.post("/api/challenges/publish")
@admin_required
def publish_challenge():
    from ..seed import apply_manifest  # reuse the same upsert path as seeding
    data = _json_body()
    try:
        norm = validate(data)
    except ManifestError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    # The "new challenge" form sets create_only so a reused slug can never
    # silently overwrite an existing challenge (and its flag).
    if data.get("create_only") and models.get_challenge_by_slug(norm["slug"]):
        return jsonify({"ok": False,
                        "error": f"A challenge with the slug '{norm['slug']}' already exists."}), 409
    challenge_id = apply_manifest(norm)
    models.audit(current_user()["id"], "challenge_publish", f"slug={norm['slug']}")
    return jsonify({"ok": True, "challenge_id": challenge_id})


@bp.post("/api/challenges/<int:challenge_id>/publish")
@admin_required
def set_published(challenge_id):
    data = _json_body()
    published = bool(data.get("published", True))
    if models.get_challenge(challenge_id) is None:
        abort(404)
    models.set_challenge_published(challenge_id, published)
    models.audit(current_user()["id"], "challenge_set_published",
                 f"id={challenge_id} published={published}")
    return jsonify({"ok": True})


@bp.post("/api/users/<int:user_id>/role")
@admin_required
def set_role(user_id):
    data = _json_body()
    role = data.get("role")
    if role not in ("student", "instructor", "administrator"):
        return jsonify({"error": "invalid role"}), 400
    if user_id == current_user()["id"]:
        # Prevents an admin locking everyone out by demoting the last admin.
        return jsonify({"error": "You can't change your own role."}), 400
    if models.get_user_by_id(user_id) is None:
        abort(404)
    models.set_user_role(user_id, role)
    models.audit(current_user()["id"], "user_set_role", f"user={user_id} role={role}")
    return jsonify({"ok": True})


@bp.get("/api/labs/running")
@admin_required
def running_labs():
    return jsonify([{"instance_id": r["id"], "user": r["username"],
                     "challenge": r["challenge_name"], "state": r["state"],
                     "expires_at": r["expires_at"]}
                    for r in models.list_running_labs()])


@bp.post("/api/labs/<instance_id>/restart")
@admin_required
def restart_lab(instance_id):
    inst = models.get_lab_instance(instance_id)
    if inst is None:
        abort(404)
    try:
        new_inst = labs.reset(inst["user_id"], instance_id)
    except labs.LabError as e:
        return jsonify({"error": e.message}), e.status
    models.audit(current_user()["id"], "lab_restart", f"instance={instance_id}")
    return jsonify({"ok": True, "instance_id": new_inst["id"]})


@bp.post("/api/labs/sweep")
@admin_required
def sweep():
    n = labs.sweep_expired()
    return jsonify({"ok": True, "cleaned": n})


@bp.get("/api/analytics")
@admin_required
def analytics():
    db = models.get_db()
    per_cat = db.execute(
        """SELECT cat.name AS category, COUNT(s.id) AS solves
           FROM categories cat
           LEFT JOIN challenges c ON c.category_id=cat.id
           LEFT JOIN solves s ON s.challenge_id=c.id
           GROUP BY cat.id ORDER BY solves DESC""").fetchall()
    hardest = db.execute(
        """SELECT c.name, c.slug, COUNT(s.id) AS solves
           FROM challenges c LEFT JOIN solves s ON s.challenge_id=c.id
           WHERE c.published=1 GROUP BY c.id ORDER BY solves ASC LIMIT 10""").fetchall()
    return jsonify({
        "platform": models.platform_stats(),
        "solves_by_category": [dict(r) for r in per_cat],
        "least_solved": [dict(r) for r in hardest],
    })


@bp.get("/api/audit")
@admin_required
def audit_log():
    return jsonify([{"user": r["username"], "action": r["action"],
                     "detail": r["detail"], "at": r["created_at"]}
                    for r in models.recent_audit(200)])
