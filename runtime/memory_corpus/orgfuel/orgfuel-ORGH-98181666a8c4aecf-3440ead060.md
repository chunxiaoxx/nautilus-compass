---
name: orgfuel-ORGH-98181666a8c4aecf-3440ead060
description: "commit 4c6e32919e49 2026-07-05 feat(compass): 7/5 conv2d_til"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-98181666a8c4aecf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 4c6e32919e49 2026-07-05
feat(compass): 7/5 conv2d_tiling_v1_002 PoC 7 件 grounded(100 题目线 第 2 题)
Computing/KernelEngineering/conv2d_tiling_v1_002/:
- Task.md (评分公式 min(100, 100*achieved_gflops/0.800))
- README.md (含 PoC 6 件 status 节 - 第 6 件 NOT grounded 同 tiled_matmul)
- baseline/init.py (naive 7-loop convolution)
- verification/{evaluate.py,_core.py} (pure stdlib import-lock)
- reference/reference.py (naive 7-loop oracle)
- data/instances.json (5 实例 conv_001..005 stride/pad 全覆盖)
- requirements.txt (stdlib only)
- frontier_eval/ 9 .txt (eval_command/eval_cwd/candidate_destination/initial_program/agent_files/readonly_files/artifact_files/constraints/copy_files)
- metrics_baseline.json + metrics.json

baseline 真跑: valid=1 combined_score=1.7156 5/5 instances (gflops~0.014)
schema 复用 til
