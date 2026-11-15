# Adding a challenge

A challenge = a **manifest** (what it is) + optionally a **lab handler** (the live
target). Two kinds:

- **Static-flag challenge** — no live target; solved by analysis/decoding of a
  shipped artifact. Needs only a manifest with a `flag`.
- **Live-lab challenge** — an interactive target. Needs a manifest referencing a
  registered `lab_kind`, plus the handler that implements it.

---

## 1. Write the manifest

Create `challenges/NN-your-slug.yaml`:

```yaml
slug: my-challenge            # lowercase kebab-case, unique
name: My Challenge
category: web                 # web | crypto | network | forensics | privesc | api
difficulty: easy              # very_easy | easy | medium | hard | insane
lab_kind: sqli_login          # 'static', or a registered live lab (see registry.py)
dynamic_flag: true            # true for live labs (per-session flag); false for static
# flag: MYCTF{...}            # REQUIRED for static challenges; FORBIDDEN for live labs
est_minutes: 20
description: >
  What the learner does.
objectives: [First objective, Second objective]
hints:
  - { level: 1, cost: 0,  body: Gentle nudge. }
  - { level: 2, cost: 10, body: Points at the component. }
  - { level: 3, cost: 20, body: Near-complete guidance (never the raw flag). }
remediation: >
  How to fix the root cause. (Unlocks after solve.)
walkthrough: >
  The intended solution path. (Unlocks after solve.)
references:
  - { title: OWASP ..., url: https://owasp.org/... }
```

Manifests are **validated** on load and on admin publish (`app/manifest.py`).
Unsafe configurations are rejected, including:

- a live lab with a shared static flag (would leak across users),
- a static challenge with no flag or a flag not matching `MYCTF{...}`,
- an unknown `lab_kind`,
- missing/invalid difficulty or points.

The validator never accepts raw SQL, shell or file paths — a manifest only
*selects* a vetted, code-reviewed `lab_kind`. It can never inject target code, so
publishing a manifest is not code execution.

Restart the app (seeding is idempotent) or publish via **Admin → Manage
Challenges → Publish from manifest** (paste the JSON equivalent).

---

## 2. (Live labs) Write the handler

1. Add `app/labs/mylab.py` subclassing `LabHandler`:

```python
from .base import LabHandler, LabResult, get_state

class MyLab(LabHandler):
    kind = "my_lab"                     # must match the manifest lab_kind
    title = "My Target"

    def provision(self, instance):      # optional: set up per-instance state
        get_state(instance["id"])["things"] = {...}

    def dispatch(self, instance, subpath, request) -> LabResult:
        # The vulnerable target. Reveal instance["flag"] only on the intended
        # exploit. NEVER validate a submitted flag here — that's the backend's job.
        return LabResult(self.page(instance, "My Target", "<h1>...</h1>"))
```

**Rules for handlers**

- Keep all per-instance mutable state in `get_state(instance["id"])` so `reset`
  and expiry clean it up.
- The target reveals `instance["flag"]` on success; it does **not** check
  submitted flags.
- Model anything that would touch the host unsafely (shell, filesystem, network)
  with a safe in-memory simulation — see `cmdinjection.py` and `traversal.py`.

2. Register it in `app/labs/registry.py`:

```python
from .mylab import MyLab
_HANDLERS = { h.kind: h for h in [ ..., MyLab() ] }
```

---

## 3. Write the solve test (required)

Add a test in `tests/test_challenges.py` that performs the intended exploit and
asserts the award. A challenge is not "done" until this passes:

```python
def test_my_challenge(client, user):
    token = user["token"]
    iid = start_lab(client, token, "my-challenge")
    r = client.get(_lab(iid), headers=auth_headers(token), query_string={...})
    flag = _find_flag(r.get_data(as_text=True))
    _solve_and_assert(client, token, "my-challenge", flag, EXPECTED_POINTS)
```

Run `python -m pytest -q` and confirm green.

---

## 4. (Optional) Add it to a learning path

Edit `LEARNING_PATHS` in `app/seed.py` to include the new slug in a path's list.
