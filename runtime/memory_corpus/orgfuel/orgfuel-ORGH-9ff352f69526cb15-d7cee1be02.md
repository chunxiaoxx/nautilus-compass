---
name: orgfuel-ORGH-9ff352f69526cb15-d7cee1be02
description: "commit db553314d6e8 2026-07-05 feat(compass): 7/5 rmsnorm_v1"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9ff352f69526cb15
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit db553314d6e8 2026-07-05
feat(compass): 7/5 rmsnorm_v1_003 PoC 7 件 grounded(100 题目线 第 3 题)
Computing/KernelEngineering/rmsnorm_v1_003/:
- Task.md (评分公式 min(100, 100*achieved_gflops/0.500))
- README.md (含 PoC 6 件 status 节 - 第 6 件 NOT grounded 同 tiled_matmul/conv2d)
- baseline/init.py (naive 3-pass RMSNorm, square→reduce→divide-and-weight)
- verification/{evaluate.py,_core.py} (pure stdlib import-lock)
- reference/reference.py (naive 3-pass oracle)
- data/instances.json (5 实例:rms_001_small/rms_002_medium/rms_003_long/rms_004_thin/rms_005_wide)
- requirements.txt (stdlib only)
- frontier_eval/ 9 .txt (eval_command/eval_cwd/candidate_destination/initial_program/agent_files/readonly_files/artifact_files/constraints/copy_files)
- metrics_baseline.json + metrics.json

baseline 真跑: valid=1 c
