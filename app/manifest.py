"""Challenge manifest loading + validation.

A challenge is defined by a versioned YAML/JSON manifest. The admin publish
workflow and the dev seeder both go through `validate()` so an unsafe or
malformed definition is rejected before it reaches the database.

Safety checks (the "reject unsafe configurations" requirement):
  * difficulty must be known; points default from the difficulty table;
  * lab_kind must be either 'static' or a registered live lab;
  * a 'static' challenge must ship a flag (so it is actually solvable), and the
    flag must match the MYCTF{...} format;
  * a live-lab challenge must be dynamic_flag (per-session) — a live lab with a
    single shared static flag is rejected, since that leaks across users;
  * no raw SQL / shell / file paths are accepted from a manifest; a manifest
    only selects a vetted, code-reviewed lab_kind. It can never inject target
    code. This is what keeps manifest publishing from becoming code execution.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .config import Config
from .labs.registry import is_live_lab

FLAG_RE = re.compile(r"^MYCTF\{[^}]+\}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,48}$")
VALID_DIFFICULTY = set(Config.DIFFICULTY_POINTS)


class ManifestError(ValueError):
    pass


def load_file(path: str | Path) -> dict:
    text = Path(path).read_text()
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ManifestError(f"{path}: manifest must be a mapping")
    return data


def validate(data: dict) -> dict:
    """Return a normalized manifest dict, or raise ManifestError."""
    if not isinstance(data, dict):
        raise ManifestError("manifest must be a JSON object")
    errors: list[str] = []

    slug = str(data.get("slug", "")).strip()
    if not SLUG_RE.match(slug):
        errors.append("slug must be lowercase kebab-case (2–49 chars)")

    name = str(data.get("name", "")).strip()
    if not name:
        errors.append("name is required")

    category = str(data.get("category", "")).strip()
    if not category:
        errors.append("category (slug) is required")

    difficulty = str(data.get("difficulty", "")).strip().lower()
    if difficulty not in VALID_DIFFICULTY:
        errors.append(f"difficulty must be one of {sorted(VALID_DIFFICULTY)}")

    lab_kind = str(data.get("lab_kind", "static")).strip()
    if lab_kind != "static" and not is_live_lab(lab_kind):
        errors.append(f"lab_kind '{lab_kind}' is not a registered lab")

    dynamic = bool(data.get("dynamic_flag", lab_kind != "static"))
    flag = data.get("flag")

    if lab_kind == "static":
        if dynamic:
            errors.append("static challenges cannot be dynamic_flag")
        if not flag:
            errors.append("static challenge must define a flag")
        elif not FLAG_RE.match(str(flag)):
            errors.append("flag must match MYCTF{...}")
    else:
        if not dynamic:
            errors.append("live-lab challenge must be dynamic_flag (per-session)")
        if flag:
            errors.append("live-lab challenge must NOT ship a shared flag")

    points = data.get("points")
    if points is None and difficulty in VALID_DIFFICULTY:
        points = Config.DIFFICULTY_POINTS[difficulty]
    if isinstance(points, bool) or not isinstance(points, int) or not 0 < points <= 10_000:
        errors.append("points must be an integer from 1 to 10000")
    if len(name) > 120:
        errors.append("name is too long (max 120)")
    if len(str(data.get("description", ""))) > 20_000:
        errors.append("description is too long (max 20000)")

    refs = data.get("references", [])
    if not isinstance(refs, list):
        errors.append("references must be a list")
    else:
        for r in refs:
            url = r.get("url") if isinstance(r, dict) else None
            if (not isinstance(url, str) or not re.match(r"^https?://", url, re.I)
                    or not isinstance(r.get("title"), str)):
                errors.append("each reference needs a title and an http(s) url")
                break
    target_url = data.get("target_url") or None
    if target_url is not None:
        if (not isinstance(target_url, str) or len(target_url) > 2048
                or not re.match(r"^https?://[^\s]+$", target_url, re.I)):
            errors.append("target_url must be an http(s) URL")
        elif lab_kind != "static":
            errors.append("target_url is only for static challenges (labs get their own URL)")
    objectives = data.get("objectives", [])
    if not isinstance(objectives, list) or not all(isinstance(o, str) for o in objectives):
        errors.append("objectives must be a list of strings")

    hints = data.get("hints", [])
    if not isinstance(hints, list):
        errors.append("hints must be a list")
    else:
        for h in hints:
            if not isinstance(h, dict) or "level" not in h or "body" not in h:
                errors.append("each hint needs level and body")
            elif (isinstance(h["level"], bool) or not isinstance(h["level"], int)
                  or isinstance(h.get("cost", 0), bool)
                  or not isinstance(h.get("cost", 0), int) or h.get("cost", 0) < 0
                  or not isinstance(h["body"], str)):
                # A negative cost would hand out free points.
                errors.append("hint level/cost must be integers (cost >= 0) and body text")

    if errors:
        raise ManifestError(f"{slug or '?'}: " + "; ".join(errors))

    return {
        "slug": slug,
        "name": name,
        "category": category,
        "category_name": data.get("category_name", category.title()),
        "skill": data.get("skill", ""),
        "difficulty": difficulty,
        "points": int(points),
        "est_minutes": data.get("est_minutes"),
        "description": str(data.get("description", "")).strip(),
        "objectives": data.get("objectives", []),
        "lab_kind": lab_kind,
        "dynamic_flag": dynamic,
        "flag": str(flag) if flag else None,
        "remediation": data.get("remediation"),
        "walkthrough": data.get("walkthrough"),
        "references": data.get("references", []),
        "target_url": target_url,
        "hints": hints,
        "published": bool(data.get("published", True)),
        "sort": int(data.get("sort", 0)),
        "version": int(data.get("version", 1)),
    }


def load_dir(directory: str | Path) -> list[dict]:
    out = []
    for path in sorted(Path(directory).glob("*.y*ml")):
        out.append((path, validate(load_file(path))))
    return out
