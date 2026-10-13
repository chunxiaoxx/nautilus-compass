---
name: orgfuel-ORGH-228659fd118761a2-f7ec9ab2d8
description: "工具决策记录 encrypt_legacy_obs.py compass v0.9.x → v1.0 · encrypt"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-228659fd118761a2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 encrypt_legacy_obs.py
compass v0.9.x → v1.0 · encrypt legacy plaintext observations.

For Pro+ users upgrading from v0.9.x: re-encrypt all existing
content_plain rows in observations table using the new master_key.

Run (interactive):
  python tools/encrypt_legacy_obs.py --user-id u_xxx
    → prompts for passphrase + encryption_salt (from signup response)
    → reads all observations WHERE user_id=? AND content_plain IS NOT NULL
    → encrypts each · sets encrypted_body + encryption_version='v1' · NULLs content_plain
    → COMMIT

Idempotent: re-running on already-encrypted obs is a no-op
(skips rows where content_plain IS NULL).

Backup automatic: copies db file to db.pre-v1-encrypt before mutation.
Stop and rollback: copy backup back · restart server.
