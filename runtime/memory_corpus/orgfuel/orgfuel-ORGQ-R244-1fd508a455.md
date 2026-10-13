---
name: orgfuel-ORGQ-R244-1fd508a455
description: "### R244 · 2026-10-06 08:5x(quiet+E1 回放发车前置探测) - **probe(08:"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R244
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R244 · 2026-10-06 08:5x(quiet+E1 回放发车前置探测)
- **probe(08:50)**:信箱 0 未读·CI×50 折叠·A100 GPU 空(14MiB/40G)
- **E1 回放前置探测 [实测]**:pipe_art 无 e1 目录(金标需从仓内 e1_judge_pack 上传或 gh 拉);vdd2 有 judge14b_smoke/judge14b_upgrade(14B 线 adapter 在)——**现役 1.7B verdict-judge adapter 待定位**(maxdepth 3 未见,可能在 vdd2 深层或本地);
- **发车 runbook(留待取)**:①定位 1.7B adapter(按判据档 greedy/v4 配置对表 e1_j2_batch_judge_3b.py 定版档)②上传金标(主包唯一 498+OOD 400,仓内 e1_main_judge_pack_498f.zip/goldpack_ood_judge_J1J2J3.tgz)③A100 回放 898 题(≤2h)→ER1-ER4 逐门裁
- M1:+0(探测+runbook;死线 10/13 余裕)
