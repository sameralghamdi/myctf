"""`flask reset-progress`: wipes solves/submissions/points, keeps accounts."""
from __future__ import annotations

import base64
import codecs
import re

from conftest import auth_headers, register, start_lab, submit_flag


def _solve(client, token):
    iid = start_lab(client, token, "encoding-decoding")
    page = client.get(f"/labs/{iid}/", headers=auth_headers(token)).get_data(as_text=True)
    blob = re.search(r'<pre id="blob">([^<]+)</pre>', page).group(1).strip()
    return submit_flag(client, token, "encoding-decoding", codecs.encode(base64.b64decode(blob).decode(), "rot_13"))


def test_reset_progress_wipes_scores_but_keeps_accounts(app, client):
    _, token = register(client, "resetme")
    assert _solve(client, token).get_json()["awarded"] == 50
    submit_flag(client, token, "sqli-login-bypass", "MYCTF{wrong}")
    assert client.get("/api/leaderboard", headers=auth_headers(token)).get_json()

    result = app.test_cli_runner().invoke(args=["reset-progress"], input="RESET\n")
    assert result.exit_code == 0, result.output
    assert "Done." in result.output

    dash = client.get("/api/dashboard", headers=auth_headers(token)).get_json()
    assert dash["score"] == 0 and dash["completed"] == 0
    assert client.get("/api/leaderboard", headers=auth_headers(token)).get_json() == []
    me = client.get("/api/session", headers=auth_headers(token)).get_json()
    assert me["user"]["username"] == "resetme"  # account and session survive
    names = {a["slug"] for a in client.get("/api/achievements", headers=auth_headers(token)).get_json() if a["earned"]}
    assert names == {"welcome"}
    # The challenge can be solved (and scored) again.
    assert _solve(client, token).get_json()["awarded"] == 50


def test_reset_progress_needs_confirmation(app, client):
    _, token = register(client, "keepme")
    _solve(client, token)
    result = app.test_cli_runner().invoke(args=["reset-progress"], input="no\n")
    assert result.exit_code != 0 and "Nothing was changed" in result.output
    assert client.get("/api/dashboard", headers=auth_headers(token)).get_json()["score"] == 50
