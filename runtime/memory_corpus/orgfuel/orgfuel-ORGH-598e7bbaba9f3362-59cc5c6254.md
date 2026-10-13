---
name: orgfuel-ORGH-598e7bbaba9f3362-59cc5c6254
description: "工具决策记录 rsi_regression_build_v1.py rsi-bench 格式回归集 v1 定版构建器(2"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-598e7bbaba9f3362
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 rsi_regression_build_v1.py
rsi-bench 格式回归集 v1 定版构建器(2026-10-08 · A 臂补齐,PR 件)。

选入判据(全实锚,零推断):
  A 臂 error 15 = django_report_a.error_ids(8) + a_eof_report.error_ids(1=sympy-13974
                  补跑后仍 apply fail 归格式,L3_BOARD_PAGE 脚注坐实)
                  + 归因简报 P3 rest 批 6 题(run_instance.log 实测 malformed)
  B 臂 error 11 = b_django/b_eof/b_rest 三报告 error_ids 并集
  合计 26 行(20 unique 题,双臂交集 6)——超外部承诺 25 的 +1 来自 A 臂补跑折入
  (sphinx-8475 补跑 resolved 移出后又由 sympy-13974 折入),如实交付不凑数。
缺陷标注(伴随特征,非选入门;口径=归因终版:malformed hunk 为主阻断,
缺尾换行为伴随特征非充分条件):
  no_trailing_newline / malformed_hunk / bad_newfile_path
patch 来源:A=preds_arm_a.json(model_patch),B=board_b/task_*/patch.diff。
输出:runtime/outreach/rsi_regression_set_v1.jsonl
