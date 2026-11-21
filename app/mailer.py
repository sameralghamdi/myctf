"""Outgoing email: sign-in codes and password-reset links.

Backends (chosen in this order):
  * ``smtp``    when MYCTF_SMTP_HOST is set (any provider: Gmail app password,
                Brevo, Resend, Amazon SES, Zoho, Mailgun…);
  * ``memory``  under TESTING: messages are appended to ``OUTBOX`` for tests;
  * ``console`` otherwise (local development): the message is printed to the
                server log so you can copy the code or link.

Sending happens on a background thread so a slow mail server never delays the
request, and response timing can't reveal whether an address is registered.
"""
from __future__ import annotations

import smtplib
import ssl
import sys
import threading
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from flask import current_app

OUTBOX: list[EmailMessage] = []


def backend(app=None) -> str:
    cfg = (app or current_app).config
    if cfg.get("SMTP_HOST"):
        return "smtp"
    return "memory" if cfg.get("TESTING") else "console"


def _build(cfg, to: str, subject: str, text: str, html: str | None) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = to
    msg["Message-ID"] = make_msgid(domain=cfg["MAIL_FROM"].rsplit("@", 1)[-1].strip("> ") or None)
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    return msg


def _deliver_smtp(cfg: dict, msg: EmailMessage) -> None:
    host, port, mode = cfg["SMTP_HOST"], cfg["SMTP_PORT"], cfg["SMTP_SECURITY"]
    context = ssl.create_default_context()
    try:
        if mode == "ssl":
            server = smtplib.SMTP_SSL(host, port, timeout=20, context=context)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
        with server:
            if mode == "starttls":
                server.starttls(context=context)
            if cfg["SMTP_USER"]:
                server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            server.send_message(msg)
    except Exception as exc:  # never crash a request because mail failed
        print(f"[mailer] could not send to {msg['To']}: {exc}", file=sys.stderr, flush=True)


def send(to: str, subject: str, text: str, html: str | None = None) -> None:
    app = current_app._get_current_object()
    cfg = {key: app.config.get(key) for key in (
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_SECURITY", "MAIL_FROM")}
    msg = _build(cfg, to, subject, text, html)
    kind = backend(app)
    if kind == "memory":
        OUTBOX.append(msg)
    elif kind == "console":
        print(f"\n===== EMAIL (dev console backend) =====\nTo: {to}\nSubject: {subject}\n\n{text}\n"
              "=======================================\n", flush=True)
    else:
        threading.Thread(target=_deliver_smtp, args=(cfg, msg), daemon=True).start()


# ------------------------------------------------------------------ templates
def _wrap(title: str, body_html: str) -> str:
    return f"""<!doctype html><html><body style="margin:0;background:#0b0f19;font-family:Arial,Helvetica,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:32px 16px">
<table role="presentation" width="100%" style="max-width:480px;background:#111827;border:1px solid #1f2937;border-radius:12px">
<tr><td style="padding:24px 28px;color:#f9fafb;font-size:18px;font-weight:bold">
<span style="display:inline-block;background:#dc2626;color:#fff;border-radius:8px;padding:2px 9px;margin-right:8px;font-family:monospace">M</span>MyCTF</td></tr>
<tr><td style="padding:0 28px 28px;color:#d1d5db;font-size:14px;line-height:22px">
<h1 style="color:#f9fafb;font-size:20px;margin:0 0 12px">{title}</h1>{body_html}</td></tr></table>
<p style="color:#6b7280;font-size:12px">You received this because of activity on your MyCTF account.</p>
</td></tr></table></body></html>"""


def send_login_code(to: str, name: str, code: str, minutes: int) -> None:
    text = (f"Hi {name},\n\nYour MyCTF sign-in code is: {code}\n\n"
            f"It expires in {minutes} minutes. If you didn't try to sign in, change your "
            "password: someone knows it.\n")
    html = _wrap("Your sign-in code", f"""<p>Hi {_esc(name)}, use this code to finish signing in:</p>
<p style="font-family:monospace;font-size:32px;letter-spacing:8px;color:#f87171;font-weight:bold;margin:20px 0">{code}</p>
<p>It expires in {minutes} minutes.</p>
<p style="color:#9ca3af">Didn't try to sign in? Change your password: someone knows it.</p>""")
    send(to, "Your MyCTF sign-in code", text, html)


def send_reset_link(to: str, name: str, link: str, minutes: int) -> None:
    text = (f"Hi {name},\n\nReset your MyCTF password with this link (valid for {minutes} minutes):\n\n"
            f"{link}\n\nIf you didn't ask for this, ignore this email; your password won't change.\n")
    html = _wrap("Reset your password", f"""<p>Hi {_esc(name)}, click the button to choose a new password.</p>
<p style="margin:24px 0"><a href="{_esc(link)}" style="background:#dc2626;color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:bold;display:inline-block">Reset password</a></p>
<p>The link is valid for {minutes} minutes and works once.</p>
<p style="color:#9ca3af;word-break:break-all">Or paste this into your browser:<br>{_esc(link)}</p>
<p style="color:#9ca3af">Didn't ask for this? Ignore this email; your password won't change.</p>""")
    send(to, "Reset your MyCTF password", text, html)


def _esc(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def public_url() -> str:
    """Base URL for links in emails: MYCTF_PUBLIC_URL, else the first allowed origin."""
    cfg = current_app.config
    if cfg.get("PUBLIC_URL"):
        return cfg["PUBLIC_URL"].rstrip("/")
    if cfg.get("ALLOWED_ORIGINS"):
        return cfg["ALLOWED_ORIGINS"][0].rstrip("/")
    from flask import request
    return request.host_url.rstrip("/")


def mask_email(email: str) -> str:
    """s****@gmail.com: enough to recognise, not enough to harvest."""
    local, _, domain = email.partition("@")
    if not domain:
        return "your email"
    return (local[0] + "•" * max(1, min(len(local) - 1, 5))) + "@" + domain
