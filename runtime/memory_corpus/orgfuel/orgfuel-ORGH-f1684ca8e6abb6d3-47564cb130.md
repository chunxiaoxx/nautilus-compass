---
name: orgfuel-ORGH-f1684ca8e6abb6d3-47564cb130
description: "commit cc2f358fb761 2026-05-06 ci · fix lint (ruff config + "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-f1684ca8e6abb6d3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit cc2f358fb761 2026-05-06
ci · fix lint (ruff config + os import) · fix integration test (PROJECTS exists check + safe stdout reconfigure) · fix npm wrapper (real package via __init__.py)
- pyproject · ruff ignore stylistic E/F rules · keep bug-catching ones · 153→0 lint
- pyproject · explicit packages=['nautilus_compass'] · removes broken find()
- __init__.py · root __init__.py makes 'pip install -e .' actually create importable nautilus_compass
- session_search · add PROJECTS.exists() guard before iterdir (parity w/ drift_history)
- 14 files · sys.stdout.reconfigure(encoding='utf-8') instead of TextIOWrapper(buffer)
  · old pattern caused buffer aliasing → 'I/O operation on closed file' under multi-import
- tests/test_e2e_encryption · add missing 'import os'
- ruff --fix · remove 36
