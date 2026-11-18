"""Scoring, hints, leaderboard, and manifest-validation tests."""
from __future__ import annotations

import base64
import codecs
import re

from conftest import auth_headers, register, start_lab, submit_flag

FLAG_RE = re.compile(r"MYCTF\{[^}]+\}")


def _solve_encoding(client, token):
    iid = start_lab(client, token, "encoding-decoding")
    page = client.get(f"/labs/{iid}/", headers=auth_headers(token)).get_data(as_text=True)
    blob = re.search(r'<pre id="blob">([^<]+)</pre>', page).group(1).strip()
    flag = codecs.encode(base64.b64decode(blob).decode(), "rot_13")
    return submit_flag(client, token, "encoding-decoding", flag)


def test_points_and_rank_update(client):
    _, token = register(client, "scorer")
    assert _solve_encoding(client, token).get_json()["awarded"] == 50
    dash = client.get("/api/dashboard", headers=auth_headers(token)).get_json()
    assert dash["score"] == 50
    assert dash["completed"] == 1
    assert dash["rank"] >= 1


def test_first_blood_only_once(client):
    _, ta = register(client, "fb_a")
    _, tb = register(client, "fb_b")
    assert _solve_encoding(client, ta).get_json()["first_blood"] is True
    assert _solve_encoding(client, tb).get_json()["first_blood"] is False


def _add_costed_hint(app, slug="sqli-login-bypass", level=2, cost=10):
    """Shipped challenges have free hints; the cost mechanism is still supported."""
    from app import models
    with app.app_context():
        cid = models.get_challenge_by_slug(slug)["id"]
        models.upsert_hint(cid, level, "A costed test hint.", cost)


def test_hint_unlock_deducts_points(app, client):
    _add_costed_hint(app)
    _, token = register(client, "hinter")
    # unlock a costed hint on sqli (level 2 costs 10)
    r = client.post("/api/challenges/sqli-login-bypass/hints/2", headers=auth_headers(token))
    assert r.status_code == 200 and r.get_json()["cost"] == 10
    assert r.get_json()["body"]
    # solving still nets positive, but score reflects the deduction
    iid = start_lab(client, token, "sqli-login-bypass")
    resp = client.post(f"/labs/{iid}/login", headers=auth_headers(token),
                       data={"username": "' OR '1'='1' -- ", "password": "x"})
    flag = FLAG_RE.search(resp.get_data(as_text=True)).group(0)
    submit_flag(client, token, "sqli-login-bypass", flag)
    dash = client.get("/api/dashboard", headers=auth_headers(token)).get_json()
    assert dash["score"] == 100 - 10  # 100 points minus the 10-point hint


def test_leaderboard_lists_solvers(client):
    _, token = register(client, "lbuser")
    _solve_encoding(client, token)
    lb = client.get("/api/leaderboard", headers=auth_headers(token)).get_json()
    assert any(row["username"] == "lbuser" for row in lb)


def test_hints_hidden_until_unlocked(app, client):
    _add_costed_hint(app)
    _, token = register(client, "peeker")
    data = client.get("/api/challenges/sqli-login-bypass",
                      headers=auth_headers(token)).get_json()
    costed = [h for h in data["hints"] if h["cost"] > 0]
    assert costed and all(h["body"] is None for h in costed if not h["unlocked"])


def test_manifest_validation_rejects_unsafe(app):
    from app.manifest import ManifestError, validate
    with app.app_context():
        # live lab must be dynamic, not a shared static flag
        try:
            validate({"slug": "bad-one", "name": "Bad", "category": "web",
                      "difficulty": "easy", "lab_kind": "sqli_login",
                      "dynamic_flag": False, "flag": "MYCTF{shared}"})
            assert False, "expected ManifestError"
        except ManifestError:
            pass
        # unknown lab kind rejected
        try:
            validate({"slug": "bad-two", "name": "Bad2", "category": "web",
                      "difficulty": "easy", "lab_kind": "no_such_lab",
                      "dynamic_flag": True})
            assert False, "expected ManifestError"
        except ManifestError:
            pass


def test_admin_can_validate_and_publish(client):
    login = client.post("/api/auth/login",
                        json={"username": "admin", "password": "ChangeMe_Admin!123"})
    token = login.get_json()["token"]
    manifest = {"slug": "starter-static", "name": "Starter Static",
                "category": "crypto", "difficulty": "very_easy",
                "lab_kind": "static", "flag": "MYCTF{static_demo}",
                "description": "demo", "hints": []}
    v = client.post("/admin/api/challenges/validate", headers=auth_headers(token),
                    json=manifest)
    assert v.status_code == 200 and v.get_json()["ok"]
    p = client.post("/admin/api/challenges/publish", headers=auth_headers(token),
                    json=manifest)
    assert p.status_code == 200 and p.get_json()["ok"]
    # a student can now solve it with the static flag
    _, stoken = register(client, "staticsolver")
    r = submit_flag(client, stoken, "starter-static", "MYCTF{static_demo}")
    assert r.get_json()["correct"] is True
