---
name: orgfuel-ORGQ-R215-4a5a810348
description: "### R215 · 2026-10-06 01:5x(B 臂收官链主轮:全量读数落定+EOF 补跑发车+#9873 判"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R215
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R215 · 2026-10-06 01:5x(B 臂收官链主轮:全量读数落定+EOF 补跑发车+#9873 判据①断点闭环)
- **probe(01:51)**:#9873 platform 判据①断点函(试金局页缺人读首检入口)·CI×50 折叠·A100 GPU 空
- **B 臂 django report 收割 [实测]**(01:49 落盘 2994B valid JSON:resolved 3/unres 2/error 6/empty 3,进程收尾 ALL DONE)→ **round1_merge 全量读数落定 [实测]**:A 7/30=23.3%(completed 内 58.3%/patch 合规 53.3%,格式 14+环境 2)/B 5/30=16.7%(50.0%/66.7%,格式 10 [推断·抽查定性]+环境 1,empty 9);配对:A 独解 3/B 独解 1/双解 4/皆未解 22;差分 +6.7pp
- **镜像 EOF 补跑发车 [实测]**:sphinx-8475+sympy-13974 双臂串行(A→B,run_id l3r1a_eof/l3r1b_eof,eval_eof.log),补跑读数回填后 Round 1 定版
- **榜页 [R1-B-*] 全填 [实测]**:B 行三档+配对矩阵+B 臂 error 归因注记(格式 10 未逐题定性,抽查轮核)
- **#9873 当轮闭环**:回函 9878(试金局页 §八补人读首检入口=mailto+三行说明+模板链接;intake 模板 v0 落仓 docs/metering/JUDGE_INTAKE_TEMPLATE_V0_20261006.md 与 assay 八件对齐;共议点=repo@commit 公开可克隆是否强制)+ack;部署唯一依赖=入口邮箱地址(
