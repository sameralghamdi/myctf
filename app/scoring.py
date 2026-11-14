"""Scoring + achievement logic, kept separate from HTTP handling.

Flag validation is authoritative here and runs ONLY on the platform backend.
Exploiting a lab reveals a per-session flag; this module decides whether a
submission is correct and whether (and how many) points to award — exactly once.
"""
from __future__ import annotations

from flask import current_app

from . import models
from .security import flag_matches_hash, flags_equal


def correct_flag_for(user_id: int, challenge) -> tuple[bool, str]:
    """Return (uses_dynamic, expected_or_empty).

    For dynamic labs the expected flag is the requester's OWN running instance
    flag — so a flag leaked from another user's instance never validates here.
    """
    if challenge["dynamic_flag"]:
        inst = models.get_user_lab(user_id, challenge["id"])
        if inst and inst["state"] == "running":
            return True, inst["flag"]
        return True, ""  # no running instance -> nothing to match
    return False, ""


def check_submission(user_id: int, challenge, submitted: str) -> dict:
    """Validate a flag submission and award points idempotently.

    Returns a dict: {correct, already_solved, awarded, first_blood, message}.
    """
    submitted = (submitted or "").strip()
    secret = current_app.config["SECRET_KEY"]

    dynamic, expected = correct_flag_for(user_id, challenge)
    if dynamic:
        correct = bool(expected) and flags_equal(submitted, expected)
    else:
        correct = flag_matches_hash(submitted, challenge["flag_hash"], secret)

    models.record_submission(user_id, challenge["id"], submitted, correct)

    if not correct:
        hint = ("" if dynamic and expected else
                " Start the lab first — the flag is tied to your live instance."
                if dynamic else "")
        return {"correct": False, "already_solved": False, "awarded": 0,
                "first_blood": False, "message": "Incorrect flag." + hint}

    if models.has_solved(user_id, challenge["id"]):
        return {"correct": True, "already_solved": True, "awarded": 0,
                "first_blood": False, "message": "Correct — already solved."}

    result = models.record_solve(user_id, challenge["id"], challenge["points"])
    if result is None:  # race: someone inserted between the check and here
        return {"correct": True, "already_solved": True, "awarded": 0,
                "first_blood": False, "message": "Correct — already solved."}

    _award_achievements(user_id, challenge, result["first_blood"])
    models.audit(user_id, "solve",
                 f"challenge={challenge['slug']} points={challenge['points']}")
    msg = "Correct! +%d points." % challenge["points"]
    if result["first_blood"]:
        msg += " 🩸 First blood!"
    return {"correct": True, "already_solved": False,
            "awarded": challenge["points"], "first_blood": result["first_blood"],
            "message": msg}


# Map a category slug to the achievement granted on first solve in it.
_CATEGORY_ACHIEVEMENTS = {
    "web": "web_rookie",
    "crypto": "cipher_breaker",
    "forensics": "forensics_analyst",
    "network": "network_investigator",
    "privesc": "privilege_climber",
}


def _award_achievements(user_id: int, challenge, first_blood: bool) -> None:
    if first_blood:
        models.grant_achievement(user_id, "first_blood")

    cat = models.get_category_by_slug(
        _category_slug_for_challenge(challenge))
    if cat:
        slug = _CATEGORY_ACHIEVEMENTS.get(cat["slug"])
        if slug:
            models.grant_achievement(user_id, slug)

    solved = len(models.user_solved_ids(user_id))
    for threshold, slug in [(1, "first_solve"), (5, "solver_5"),
                            (10, "solver_10"), (25, "solver_25")]:
        if solved >= threshold:
            models.grant_achievement(user_id, slug)


def _category_slug_for_challenge(challenge) -> str:
    cat = models.get_challenge(challenge["id"])
    row = models.get_db().execute(
        "SELECT slug FROM categories WHERE id=?", (challenge["category_id"],)
    ).fetchone()
    return row["slug"] if row else ""
