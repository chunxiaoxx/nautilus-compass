---
name: orgfuel-ORGH-793b60e32487f151-6dff25abd9
description: "commit 177f835f52e2 2026-05-21 fix(ci): ruff F401 unused imp"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-793b60e32487f151
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 177f835f52e2 2026-05-21
fix(ci): ruff F401 unused imports · 47 errors → 0
CI Lint step failed on commit fbceaa6 (run #26263782648).
Auto-fix via `ruff check --fix` removed 44 unused imports across 26 files
(v2 subpackages, tests, ops, examples). Remaining 3 inside try/except
import blocks for relative-then-absolute fallback get `# noqa: F401`.

Verified post-fix:
  - ruff check . → All checks passed
  - tests/test_integration_e2e.py · 12/12 PASS · cross-module data flow ok
  - v2 subpackage imports still work (storage/proof/drift/recall_pkg/
    skills_pkg/judges all import cleanly from plugin dir)

Files touched: 26 (44 imports removed, 4 noqa added)
