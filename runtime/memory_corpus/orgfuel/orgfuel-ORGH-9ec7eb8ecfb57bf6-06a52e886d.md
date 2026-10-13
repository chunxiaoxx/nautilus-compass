---
name: orgfuel-ORGH-9ec7eb8ecfb57bf6-06a52e886d
description: "commit be4efe9dbce0 2026-05-19 fix(packaging): v1.6.3 · v1.6"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9ec7eb8ecfb57bf6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit be4efe9dbce0 2026-05-19
fix(packaging): v1.6.3 · v1.6.2 was broken — sdk/middleware not included
Root cause: pyproject.toml `packages = ["nautilus_compass"]` only included
top-level, so `from nautilus_compass.sdk.attach_memory import attach_memory`
failed at install time (ModuleNotFoundError: nautilus_compass.sdk).

Verified broken via fresh `pip install nautilus-compass==1.6.2`:
- `dir(nautilus_compass)` only has __version__ · 0 submodules
- All 6 console scripts (compass-mcp / compass-drift-history / etc) broken

Fix:
- pyproject.toml: packages list now includes nautilus_compass.sdk +
  nautilus_compass.middleware; package-dir maps each to its source subdir
- sdk/__init__.py: created (re-exports attach_memory for public API)
- __init__.py: __version__ synced 1.5.1 → 1.6.3 (was sta
