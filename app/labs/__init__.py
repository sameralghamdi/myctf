"""Lab orchestrator — the dev stand-in for the production lab controller.

Responsibilities mirror the production orchestrator from the spec:
  * authorize + resource-limit lab creation
  * generate a unique per-session flag
  * provision an isolated environment (here: in-process handler state)
  * expose start / stop / reset / get
  * expire and clean up instances

In production each start() would call out to a container/microVM controller and
return a routable, network-isolated URL instead of an in-process handler. The
interface is kept narrow so that swap is localized.
"""
from __future__ import annotations

from flask import current_app

from .. import models
from ..security import new_id, random_flag
from .registry import get_handler, is_live_lab


class LabError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def _flag_label(challenge) -> str:
    # Neutral on purpose: slugs name the technique (and the track), flags must not.
    return f"case_{challenge['id']}"


def start(user_id: int, challenge) -> dict:
    """Start (or return the existing) lab instance for this user+challenge."""
    kind = challenge["lab_kind"]
    if not is_live_lab(kind):
        raise LabError("This challenge has no live lab.", 400)

    existing = models.get_user_lab(user_id, challenge["id"])
    if existing and existing["state"] == "running":
        return dict(existing)

    if existing:  # stopped/expired row lingering -> clear it
        get_handler(kind).teardown(existing["id"])
        models.delete_lab_instance(existing["id"])

    # resource guard
    if models.count_running_labs(user_id) >= current_app.config["LAB_MAX_PER_USER"]:
        raise LabError("Too many running labs. Stop one first.", 429)

    instance_id = new_id(16)
    flag = random_flag(_flag_label(challenge))
    ttl = current_app.config["LAB_TTL"]
    lab_url = f"/labs/{instance_id}/"
    models.create_lab_instance(instance_id, challenge["id"], user_id, flag, ttl,
                               lab_url=lab_url, container_ref="inproc")
    instance = models.get_lab_instance(instance_id)
    get_handler(kind).provision(instance)
    models.audit(user_id, "lab_start",
                 f"challenge={challenge['slug']} instance={instance_id}")
    return dict(instance)


def stop(user_id: int, instance_id: str) -> None:
    instance = models.get_lab_instance(instance_id)
    if instance is None:
        raise LabError("No such lab.", 404)
    if instance["user_id"] != user_id:
        raise LabError("Not your lab.", 403)
    challenge = models.get_challenge(instance["challenge_id"])
    handler = get_handler(challenge["lab_kind"])
    if handler:
        handler.teardown(instance_id)
    models.delete_lab_instance(instance_id)
    models.audit(user_id, "lab_stop", f"instance={instance_id}")


def reset(user_id: int, instance_id: str) -> dict:
    """Tear down and recreate with a fresh flag + clean state."""
    instance = models.get_lab_instance(instance_id)
    if instance is None:
        raise LabError("No such lab.", 404)
    if instance["user_id"] != user_id:
        raise LabError("Not your lab.", 403)
    challenge = models.get_challenge(instance["challenge_id"])
    stop(user_id, instance_id)
    return start(user_id, challenge)


def get_owned(user_id: int, instance_id: str):
    instance = models.get_lab_instance(instance_id)
    if instance is None or instance["user_id"] != user_id:
        return None
    return instance


def sweep_expired() -> int:
    """Expire + clean up overdue instances. Returns count cleaned."""
    n = 0
    for inst in models.expired_lab_instances():
        challenge = models.get_challenge(inst["challenge_id"])
        if challenge:
            handler = get_handler(challenge["lab_kind"])
            if handler:
                handler.teardown(inst["id"])
        models.set_lab_state(inst["id"], "expired")
        models.delete_lab_instance(inst["id"])
        n += 1
    return n
