"""Isolation & authorization boundary tests (the spec's security requirements):
users cannot reach another user's lab, and a flag leaked from one user's
instance cannot score for another user.
"""
from __future__ import annotations

import re

from conftest import auth_headers, register, start_lab, submit_flag

FLAG_RE = re.compile(r"MYCTF\{[^}]+\}")


def test_cannot_access_another_users_lab(client):
    _, token_a = register(client, "alice")
    _, token_b = register(client, "bob")
    iid_a = start_lab(client, token_a, "sqli-login-bypass")
    # Bob tries to reach Alice's lab instance by its id -> forbidden
    r = client.get(f"/labs/{iid_a}/", headers=auth_headers(token_b))
    assert r.status_code == 403


def test_leaked_flag_does_not_score_for_other_user(client):
    _, token_a = register(client, "carol")
    _, token_b = register(client, "dave")
    iid_a = start_lab(client, token_a, "idor-profile-access")
    # Alice legitimately captures HER instance flag
    resp = client.get(f"/labs/{iid_a}/api/account/1002", headers=auth_headers(token_a))
    alice_flag = FLAG_RE.search(resp.get_data(as_text=True)).group(0)
    # Bob starts his OWN instance (different flag) and tries Alice's flag
    start_lab(client, token_b, "idor-profile-access")
    r = submit_flag(client, token_b, "idor-profile-access", alice_flag)
    assert r.get_json()["correct"] is False  # per-session flags defeat sharing


def test_submit_without_running_lab_is_helpful(client):
    _, token = register(client, "erin")
    r = submit_flag(client, token, "sqli-login-bypass", "MYCTF{anything}")
    body = r.get_json()
    assert body["correct"] is False
    assert "Start the lab" in body["message"]


def test_lab_is_bound_one_per_user_challenge(client):
    _, token = register(client, "frank")
    iid1 = start_lab(client, token, "reflected-xss")
    iid2 = start_lab(client, token, "reflected-xss")
    assert iid1 == iid2  # starting again returns the same instance


def test_reset_rotates_the_flag(client):
    _, token = register(client, "grace")
    iid = start_lab(client, token, "path-traversal")
    f1 = FLAG_RE.search(client.get(
        f"/labs/{iid}/", headers=auth_headers(token),
        query_string={"file": "../secret/flag.txt"}).get_data(as_text=True)).group(0)
    reset = client.post(f"/api/labs/{iid}/reset", headers=auth_headers(token))
    iid2 = reset.get_json()["instance_id"]
    f2 = FLAG_RE.search(client.get(
        f"/labs/{iid2}/", headers=auth_headers(token),
        query_string={"file": "../secret/flag.txt"}).get_data(as_text=True)).group(0)
    assert f1 != f2  # a fresh instance has a fresh flag


def test_answers_not_exposed_in_metadata(client):
    _, token = register(client, "heidi")
    # challenge detail before solving must not leak remediation/walkthrough/flag
    r = client.get("/api/challenges/sqli-login-bypass", headers=auth_headers(token))
    data = r.get_json()
    assert "walkthrough" not in data
    assert "remediation" not in data
    assert "flag" not in data and "flag_hash" not in data


def test_walkthrough_unlocks_after_solve(client):
    import base64, codecs
    _, token = register(client, "ivan")
    iid = start_lab(client, token, "encoding-decoding")
    page = client.get(f"/labs/{iid}/", headers=auth_headers(token)).get_data(as_text=True)
    blob = re.search(r'<pre id="blob">([^<]+)</pre>', page).group(1).strip()
    flag = codecs.encode(base64.b64decode(blob).decode(), "rot_13")
    submit_flag(client, token, "encoding-decoding", flag)
    r = client.get("/api/challenges/encoding-decoding", headers=auth_headers(token))
    assert r.get_json().get("walkthrough")  # now present
