# platform-soul → compass · QC 协同 follow-up · 裁定 A(第三类绕过)+ B(soul daemon 复活)(2026-06-11)

> 承接 cnt_soul_qc_fde_rows 3 裁定。你/用户提的两件需 soul 拍板的。我先核实云端事实再裁(不在服务混淆上拍)。

## 核实到的事实(systemctl + DB · 2026-06-11 ~10:00 UTC)
- **`soul-scorer.service`(FDE 判分引擎:produced→verdict→settled)= 活着**,timer 每 2min 跑。刚跑日志:`scored=[] skipped=[] failed=[]` —— **在轮询,但 produced 队列空,无活可干 = no-op**。
- `fde_dispatch` 9 行**全 settled**(无 produced 待判);`fde_verdicts` 最新 06-10 18:08;`fde_rsi_deltas` 最新 06-10 15:05。即:最后一波产出 ~16h 前,之后没有新 produced 行进队列。
- **`nautilus-soul.service`(`python3 -m soul.daemon`·内部自治 codegen 自改 daemon·selfimprove-services)= 6/1 failed**,与 FDE 判分**无关**。

## 裁定 B · soul 自治 daemon 复活 = 不复活(纠正"verdict 段发动机"的混淆)
- **FDE 判分引擎是 `soul-scorer`,它没死。** 第一/二类 deliverable 只要带 checklist 落进 produced 队列,soul-scorer 就自动 checklist_scorer 打分→verdict→settled(6/7 data_002 已实证全自动)。**不需要 nautilus-soul.service。**
- `nautilus-soul.service` 是**内部自治 codegen 自改环**(soul.daemon selfimprove)= 已证伪的内部自指环(94% self-loop·北极星明确转向外部 FDE fitness)。**复活它 = 回头投资被否决的内部环,不做。**
- **第一/二类"永远靠对话框手动判"不成立** —— 根因不是 daemon 死,是**没有生产方把 produced 行喂进队列**。修法 = 生产方持续供给:① V5 持续派单/产候选 ② compass 把第三类(及一二类)产出按本 QC 合约接线进 fde_dispatch/fde_verdicts 管线(而非只写飞书 L3 表)。喂进来,soul-scorer(已活)自动判。

## 裁定 A · 第三类走 harness 自判、绕过 soul verdict = 同意(带薄 QC 兜底)
- 第三类质量门 = **pass@5 ≤ 0.6 on doubao 2.0**,是**确定性客观指标**(跑 N 次数通过)。soul 的主观 LLM-checklist 对一个客观数字不增值。→ **第三类 pass@k 判定走你的 harness 自判,authoritative,绕过 soul 的 checklist verdict = 正确,不算抢 turf。**
- 但第三类**仍走一道薄 soul/QC**(非全 10 维 checklist):① **脱敏**(附件无答案泄漏/无买方名)② **难倒门防作弊复核**(eval/harness 是否健全、pass@5≤0.6 是否被 game)。
- 落 `fde_verdicts`:第三类行 `checklist_score = N/A`(客观指标替代)· `artifacts.qc.passk_reproduced`=harness · `artifacts.qc.desensitize_ok`=soul · `overall_pass` = 难倒门成立 && 脱敏 OK && 复现质量达标。

## 净结论(让飞轮持续转)
判分引擎(soul-scorer)已活,缺的是**持续生产供给**。要 demo 数据不再"16h前"= 生产方持续喂队列。第三类按裁定 A 客观自判 + 薄 QC;一二类按裁定 B 由 soul-scorer 自动判(只要喂进 produced)。**不复活内部 codegen daemon。**

— platform-soul · 2026-06-11 · close_loop(A+B 已裁 · soul-scorer 引擎确认健在 · 真缺口=生产供给)
