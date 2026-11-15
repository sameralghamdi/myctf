"""In-process sliding-window rate limiter (dev). Production uses Redis so limits
hold across workers; the interface here matches that intent.
"""
from __future__ import annotations

import threading
import time

_HITS: dict[str, list[float]] = {}
_LOCK = threading.Lock()


_MAX_KEYS = 20_000


def _prune(now: float, horizon: int = 3600) -> None:
    """Drop stale buckets so attacker-chosen keys can't grow memory forever."""
    for k in [k for k, v in _HITS.items() if not v or v[-1] < now - horizon]:
        del _HITS[k]


def allow(key: str, limit: int, window: int) -> bool:
    now = time.time()
    with _LOCK:
        if len(_HITS) > _MAX_KEYS:
            _prune(now)
        bucket = _HITS.setdefault(key, [])
        cutoff = now - window
        bucket[:] = [t for t in bucket if t >= cutoff]
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


def peek(key: str, limit: int, window: int) -> bool:
    """True if `key` is still under its limit. Does NOT record a hit."""
    cutoff = time.time() - window
    with _LOCK:
        return sum(1 for t in _HITS.get(key, []) if t >= cutoff) < limit


def reset(key: str | None = None) -> None:
    with _LOCK:
        if key is None:
            _HITS.clear()
        else:
            _HITS.pop(key, None)
