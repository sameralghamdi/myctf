"""Idempotent seeding: categories, achievements, challenges (from manifests),
learning paths, and a bootstrap administrator. Safe to run on every startup.
"""
from __future__ import annotations

from flask import current_app

from . import models
from .config import CHALLENGE_DIR
from .manifest import load_dir
from .security import hash_flag, hash_password

# Canonical categories -> dashboard skill + ordering.
CATEGORIES = [
    ("web", "Web Application", "Web Security", 1),
    ("crypto", "Cryptography", "Cryptography", 2),
    ("network", "Network", "Network Security", 3),
    ("forensics", "Forensics", "Forensics", 4),
    ("privesc", "Privilege Escalation", "Privilege Escalation", 5),
    ("api", "API Security", "API Security", 6),
    ("linux", "Linux", "Linux", 7),
]

ACHIEVEMENTS = [
    ("welcome", "Welcome Aboard", "Created your MyCTF account", "user-plus"),
    ("first_solve", "First Steps", "Solved your first challenge", "flag"),
    ("first_blood", "First Blood", "Were first to solve a challenge", "droplet"),
    ("web_rookie", "Web Rookie", "Solved a web challenge", "globe"),
    ("cipher_breaker", "Cipher Breaker", "Solved a crypto challenge", "key"),
    ("forensics_analyst", "Forensics Analyst", "Solved a forensics challenge", "search"),
    ("network_investigator", "Network Investigator", "Solved a network challenge", "share-2"),
    ("privilege_climber", "Privilege Climber", "Solved a privesc challenge", "trending-up"),
    ("solver_5", "Getting Warm", "Solved 5 challenges", "zap"),
    ("solver_10", "On a Roll", "Solved 10 challenges", "award"),
    ("solver_25", "Seasoned", "Solved 25 challenges", "star"),
]

LEARNING_PATHS = [
    ("fundamentals", "Cybersecurity Fundamentals", "beginner",
     "Start here: HTTP, Linux, encoding, and your first exploits.",
     ["http-basics", "linux-basics", "encoding-decoding", "sqli-login-bypass",
      "reflected-xss"]),
    ("web-pentest", "Web Penetration Testing", "intermediate",
     "Core web attack classes against live targets.",
     ["sqli-login-bypass", "reflected-xss", "stored-xss", "idor-profile-access",
      "path-traversal", "insecure-file-upload", "command-injection"]),
    ("auth-and-api", "Auth & API Security", "intermediate",
     "Break authentication, authorization, and API object access.",
     ["weak-password-reset", "jwt-authorization-flaw", "api-bola",
      "idor-profile-access"]),
    ("blue-and-systems", "Forensics & Systems", "intermediate",
     "Investigate captured traffic and escalate on Linux.",
     ["pcap-investigation", "linux-basics", "linux-privesc"]),
]


def apply_manifest(norm: dict) -> int:
    """Upsert a validated manifest into the DB. Returns challenge id."""
    cat = models.get_category_by_slug(norm["category"])
    if cat is None:
        cat_id = models.upsert_category(norm["category"],
                                        norm.get("category_name", norm["category"].title()),
                                        norm.get("skill", ""))
    else:
        cat_id = cat["id"]

    flag_hash = None
    if norm["lab_kind"] == "static" and norm["flag"]:
        flag_hash = hash_flag(norm["flag"], current_app.config["SECRET_KEY"])

    challenge_id = models.upsert_challenge({
        "slug": norm["slug"], "name": norm["name"], "category_id": cat_id,
        "difficulty": norm["difficulty"], "points": norm["points"],
        "est_minutes": norm["est_minutes"], "description": norm["description"],
        "objectives": norm["objectives"], "lab_kind": norm["lab_kind"],
        "flag_hash": flag_hash, "dynamic_flag": norm["dynamic_flag"],
        "remediation": norm["remediation"], "walkthrough": norm["walkthrough"],
        "references": norm["references"], "published": norm["published"],
        "target_url": norm["target_url"],
        "sort": norm["sort"],
    })
    for h in norm["hints"]:
        models.upsert_hint(challenge_id, int(h["level"]), h["body"],
                           int(h.get("cost", 0)))
    models.prune_hints(challenge_id, [int(h["level"]) for h in norm["hints"]])
    return challenge_id


def seed_all(app) -> None:
    with app.app_context():
        for slug, name, skill, sort in CATEGORIES:
            models.upsert_category(slug, name, skill, sort)
        for slug, name, desc, icon in ACHIEVEMENTS:
            models.upsert_achievement(slug, name, desc, icon)

        # challenges from manifests
        for _path, norm in load_dir(app.config.get("CHALLENGE_DIR", CHALLENGE_DIR)):
            apply_manifest(norm)

        # learning paths
        for slug, name, level, desc, chal_slugs in LEARNING_PATHS:
            pid = models.upsert_learning_path(slug, name, level, desc)
            for i, cs in enumerate(chal_slugs):
                c = models.get_challenge_by_slug(cs)
                if c:
                    models.set_path_item(pid, c["id"], i)

        _seed_admin(app)


def _seed_admin(app) -> None:
    username = app.config["SEED_ADMIN_USER"]
    if models.get_user_by_username(username):
        return
    password = app.config["SEED_ADMIN_PASSWORD"]
    if not password:
        import secrets
        import sys
        password = secrets.token_urlsafe(12)
        print("\n" + "=" * 62 +
              f"\n  MyCTF admin account created.\n    username: {username}\n"
              f"    password: {password}\n"
              "  Shown only this once. Set MYCTF_ADMIN_PASSWORD to choose your own.\n"
              + "=" * 62 + "\n", file=sys.stderr, flush=True)
    uid = models.create_user(
        username, app.config["SEED_ADMIN_EMAIL"],
        hash_password(password,
                      iterations=app.config["PBKDF2_ITERATIONS"]),
        role="administrator", email_verified=True)
    models.audit(uid, "seed_admin", f"username={username}")
