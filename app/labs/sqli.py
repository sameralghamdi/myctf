"""SQL Injection — Login Bypass (intentionally vulnerable TRAINING target).

The login query below is built by string concatenation on purpose: this is the
teaching target. It runs against a throwaway in-memory SQLite DB created per lab
instance, seeded with synthetic users only. Exploiting it reveals the
per-instance flag; it grants nothing on the real platform.

Intended solution: a payload such as  ' OR '1'='1' --  in the username bypasses
authentication and logs the learner in as the admin account, whose profile shows
the flag.

Remediation (taught post-solve): use parameterised queries / prepared statements;
never interpolate user input into SQL.
"""
from __future__ import annotations

import html
import sqlite3

from .base import LabHandler, LabResult, get_state


class SqliLoginLab(LabHandler):
    kind = "sqli_login"
    title = "AcmeCorp Intranet — Login"

    def _lab_db(self, instance) -> sqlite3.Connection:
        st = get_state(instance["id"])
        conn = st.get("db")
        if conn is None:
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.executescript(
                """CREATE TABLE users(
                       id INTEGER PRIMARY KEY, username TEXT, password TEXT,
                       role TEXT, secret_note TEXT);"""
            )
            conn.executemany(
                "INSERT INTO users(username,password,role,secret_note) VALUES (?,?,?,?)",
                [
                    ("admin", "S3cur3!tr0ub4dor&3", "administrator",
                     f"Internal admin console key: {instance['flag']}"),
                    ("j.rivera", "hunter2", "staff", "Remember to file the Q3 report."),
                    ("m.okafor", "letmein99", "staff", "Lunch menu is in the shared drive."),
                ],
            )
            conn.commit()
            st["db"] = conn
        return conn

    def provision(self, instance) -> None:
        self._lab_db(instance)  # warm the per-instance DB

    def teardown(self, instance_id: str) -> None:
        st = get_state(instance_id)
        conn = st.get("db")
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        super().teardown(instance_id)

    def dispatch(self, instance, subpath: str, request) -> LabResult:
        if request.method == "POST" and subpath in ("", "login"):
            return self._login(instance, request)
        return LabResult(self._form(instance))

    def _form(self, instance, message: str = "", ok: bool = False) -> str:
        banner = ""
        if message:
            cls = "flag" if ok else "err"
            banner = f'<div class="card"><p class="{cls}">{message}</p></div>'
        body = f"""
<h1>AcmeCorp Intranet</h1>
<p class="muted">Staff sign-in. Unauthorized access is prohibited.</p>
{banner}
<div class="card">
  <form method="post" action="{self.base_url(instance)}/login">
    <label>Username</label>
    <input name="username" autocomplete="off" autofocus>
    <label>Password</label>
    <input name="password" type="password" autocomplete="off">
    <button type="submit">Sign in</button>
  </form>
</div>
"""
        return self.page(instance, "AcmeCorp Login", body)

    def _login(self, instance, request) -> LabResult:
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = self._lab_db(instance)

        # --- INTENTIONALLY VULNERABLE QUERY (training target) ---------------
        query = (
            "SELECT * FROM users WHERE username = '%s' AND password = '%s'"
            % (username, password)
        )
        try:
            row = conn.execute(query).fetchone()
        except sqlite3.Error as e:
            # Verbose SQL errors are themselves part of the lesson (error-based).
            return LabResult(self._form(instance, f"SQL error: {html.escape(str(e))}"))

        if row is None:
            return LabResult(self._form(instance, "Invalid credentials."))

        note = html.escape(row["secret_note"] or "")
        uname = html.escape(row["username"] or "")
        role = html.escape(row["role"] or "")
        msg = (f"Signed in as <b>{uname}</b> (role: {role}). "
               f"Profile note: {note}")
        return LabResult(self._form(instance, msg, ok=True))
