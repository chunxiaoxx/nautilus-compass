# 设计 · compass 两条卖点"真闭合"复核 + 对外文档一致性 · 2026-07-08

> 前提校正(实测,非引文档):两条卖点在 v2.3.0 **大半已闭合**。以下按真实剩余缺口设计。
> 证据:`audit_kpi.py` 实测 act-on=0.178(非陈旧 README 的 0.012);`daemon.py:255` 调 `promote_lifecycle_tier`;`stop_hook.py:313` 已接 auto_ack;`recall.py:1417` reinforce_on_recall_hit。

## ① 4-tier 生命周期 · 真实缺口 = tier 驱动从没调度过
- 已闭合:生产 recall 路径 reinforce_count bump + PoI candidate emit + archived-check(daemon)。
- **缺口**:`scripts/tier_promotion_driver.py`(docstring "Cron once daily")cron-ready 但无 `tier_promotion_log.jsonl` = 从没跑过 → 全量每日晋升未发生。
- **设计**:(a) 先跑一次 driver 验证产出 log + 无异常;(b) 挂调度 —— repo 自约定"DEPLOY = separate gated ops step",故只**产调度件**(systemd `.timer` 或 Windows 计划任务模板),真挂载由用户/部署环境定;(c) 加一条 test 断言 driver dry-run 产 log。
- 风险:driver 改 session_*.md frontmatter(tier/reinforce)。低,但记忆非 git 版控 → 先 dry-run 模式验证再实跑。

## ② drift 拦截环 · 真实缺口 = 检测器 52% 误报(不是接线)
- 已闭合:auto_ack 接线,act-on 可测 0.178。
- **缺口**:152 acks 里 **79 = fp**(52%)→ agent 理性 tune out → act-on 上不去。降 act-on↔降 fp 是同一件事。
- **设计(fresh session · 真工程)**:
  1. 分析 79 个 fp 的 embedding 模式(哪些正/负锚点误触)。
  2. 调 25 正/35 负锚点 或阈值(NEG_ANCHOR 0.538 / COSINE_MIN 0.35)。
  3. **held-out 复验**:`eval_drift_holdout.py` 跑,断言 AUC 不低于 0.83 baseline(防为降 fp 牺牲召回)。
  4. 目标:fp 率下降 + AUC 保持 → act-on 自然上行。**不承诺 0.70**(那取决于 agent 行为,非纯代码可保证)。
- 🔴 **R3**:此项在 marathon session 尾部不做,fresh session 带此设计执行。

## ③ 对外文档一致性 · 真实缺口 = 版本 5 套 + 成本/AUC 打架 + 反而低估
- **P0 版本统一到 2.3.0**(单一源 = pyproject):中文 README 徽章 `1.0.0_stable`→`2.3.0`;英文 README "What's new" 头条补 2.2.0/2.3.0;paper/ 安装命令 `==1.0.0/1.1.0`→`==2.3.0`;网页 v0.9.0-dev(网页非 repo 内,另通报)。
- **P1 口径统一**:成本定一个数(注区域差);drift AUC 对外统一标 "0.83 held-out"(0.92 是 in-set,标注清楚)。
- **P1 招牌诚实**:README "activation in progress" 措辞按实测更新为"v2.3.0 已接生产 recall"(**现在是 understate,该上修不是下修**)。
- 风险:低(文档改)。可本 session 做 P0 版本硬伤。⚠️ 甲方保密:不往公开 repo 加 FDE 叙事。

## 执行顺序
1. 本 session:③ P0 版本统一(verifiable)+ ① driver dry-run 验证 + 产调度件。
2. Fresh session:② drift fp 降(带 held-out 复验)+ ③ 剩余口径/招牌措辞。

关联 [[reference_compass_full_capability_map_grounded_20260708]] · [[feedback_probe_compass_state_dont_quote_stale_docs_20260708]]
