---
name: orgfuel-ORGG-e479b8f1adbbe4e9-64a7fb5f96
description: "判读档判例 2026-06-03-p5-v14-poi-emission · Task 3: Deploy to clo"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-e479b8f1adbbe4e9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission · Task 3: Deploy to cloud + e2e verify (@verification-before-completion)
## Task 3: Deploy to cloud + e2e verify (@verification-before-completion)

No new code — deployment + real-endpoint verification. Do NOT claim done without the SSH-cat evidence.

**Step 1: Back up + dry-import the patch on cloud**

```bash
scp ops/patch_v14_recall_poi_candidate.py cloud:/tmp/patch_poi.py
ssh cloud 'cp /home/ubuntu/compass/compass_http_v09.py /home/ubuntu/compass/compass_http_v09.py.bak.pre_poi_$(date +%s) && python3 -c "import ast,sys; ast.parse(open(\"/home/ubuntu/compass/compass_http_v09.py\").read()); print(\"parses OK\")"'
```

**Step 2: Apply patch on a copy + verify it compiles BEFORE touching live**

```bash
ssh cloud 'cp /home/ubuntu/compass/compass_http_v0
