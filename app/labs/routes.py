"""The ``/labs`` blueprint: the ONLY place intentionally vulnerable targets are
served. It is deliberately separate from the platform API and auth.

Isolation enforced here:
  * the instance id in the URL is an unguessable routing token;
  * the lab is bound to a user — a signed-in non-owner is refused (anonymous
    callers holding the unguessable URL, e.g. curl, are allowed);
  * expired instances are swept before dispatch;
  * responses carry hardening headers and a banner marking them as lab content.

A lab response may set its own content-type/status/headers via LabResult.
"""
from __future__ import annotations

from flask import Blueprint, Response, abort, g

from .. import models
from . import sweep_expired
from .registry import get_handler

bp = Blueprint("labs", __name__, url_prefix="/labs")


@bp.route("/<instance_id>/", defaults={"subpath": ""},
          methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@bp.route("/<instance_id>/<path:subpath>",
          methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def lab_dispatch(instance_id: str, subpath: str):
    from ..auth import current_user  # local import avoids a cycle

    sweep_expired()
    user = current_user()

    instance = models.get_lab_instance(instance_id)
    if instance is None:
        abort(404, "Lab instance not found or expired.")
    # The unguessable instance id is a capability: it lets learners use plain
    # `curl <lab-url>` without a session cookie. A *signed-in* user who is not
    # the owner is still refused, and flags are per-instance and validated
    # per-user by the core API, so a shared URL cannot score for anyone else.
    if user is not None and instance["user_id"] != user["id"]:
        # Core isolation guarantee: you cannot touch another user's lab.
        abort(403, "This lab instance belongs to another user.")

    challenge = models.get_challenge(instance["challenge_id"])
    handler = get_handler(challenge["lab_kind"])
    if handler is None:
        abort(404, "No live lab for this challenge.")

    from flask import request
    result = handler.dispatch(instance, subpath, request)

    resp = Response(result.body, status=result.status,
                    content_type=result.content_type)
    # Harden lab responses so lab content can't be framed into the platform and
    # browsers don't sniff types. (In prod the lab is also network-isolated.)
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-MyCTF-Lab"] = instance_id
    # Same-origin form posts must carry their real Origin (with the platform-wide
    # "no-referrer" they send "Origin: null" and the CSRF guard rejects them).
    resp.headers["Referrer-Policy"] = "same-origin"
    for k, v in result.headers.items():
        resp.headers[k] = v
    return resp
