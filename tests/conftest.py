"""Shared pytest fixtures.

Each test gets a fresh app backed by an isolated in-memory SQLite database, and
module-level in-process state (lab state, rate limiter) is reset between tests.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app          # noqa: E402
from app.config import TestConfig   # noqa: E402
from app.labs import base as labbase  # noqa: E402
from app import limiter             # noqa: E402


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    yield application


@pytest.fixture(autouse=True)
def _reset_process_state():
    labbase._STATE.clear()
    limiter.reset()
    yield
    labbase._STATE.clear()
    limiter.reset()


@pytest.fixture()
def client(app):
    return app.test_client()


# --------------------------------------------------------------- helpers ----
_counter = {"n": 0}


def register(client, username: str | None = None, password: str = "Sup3rSecret!x9"):
    """Register a fresh user via the JSON API and return (username, token)."""
    if username is None:
        _counter["n"] += 1
        username = f"user{_counter['n']}"
    resp = client.post("/api/auth/register", json={
        "username": username, "email": f"{username}@test.local",
        "password": password,
    })
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return username, resp.get_json()["token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def start_lab(client, token, slug: str) -> str:
    resp = client.post(f"/api/challenges/{slug}/lab/start", headers=auth_headers(token))
    assert resp.status_code == 200, resp.get_data(as_text=True)
    return resp.get_json()["instance_id"]


def submit_flag(client, token, slug: str, flag: str):
    return client.post(f"/api/challenges/{slug}/submit",
                       headers=auth_headers(token), json={"flag": flag})


@pytest.fixture()
def user(client):
    username, token = register(client)
    return {"username": username, "token": token}
