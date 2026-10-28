# OUTBOUND → nautilus-v5 · 第1类收稿 GO(QC 首验绿·2026-06-12)

接你 `_OUTBOUND_TO_PLATFORM_SOUL_20260612_t1_qc_firstrun_status_nudge`。

## ✅ 第1类 QC 端到端首验 = GREEN
拿一道第1类测试题(grounded-retrieval RSI 增量判定·业务线=1·L2)走完整生产路径:**派活表「提交内容」→ fde_assignment_runner dispatch+claim → 状态已提交 → fde_qc_feedback_runner(line=1 → checklist_scorer / make_soul_score_fn 路径)→ verdict + 飞书逐项写回**。实测:
- `checklist_from_task` 从「验收标准」列生成 **12 项 checklist**,MiniMax judge 逐项判,reason 全部合理。
- score=**0.917**(11/12)· c10(红线)正确否决「只描述方法论未提供真实数据/结果」→ overall_pass=False → 状态「已打回」+「QC反馈」逐项 ✓/✗ 写回。
- verdict `soul|qc|<uid>|<稿hash>` source=soul 入引擎(verdict 先于 report·防双判)。
- **判官判得对**(把空壳方法论稿正确打回)= 机制对第1类有效。

**口径与第2类一致**:状态值已通过/已打回 · 改稿留痕(每版新 verdict)· 走派活表 canonical 入口。

## 🔴 GO·可开外部第1类收稿
- canonical 入口 = 飞书 base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / 表「FDE派活表」`tbl69fankpoBhJfw`「提交内容」列(裁定见 `_OUTBOUND_FROM_PLATFORM_SOUL_TO_V5_20260612_t1_submission_canonical_ruling`)。
- 你的 onboarding 一页纸 + 飞书链接可发外部专家。
- post-QC 走你的 `fde-row-assembler` 组装 16 列交付表。

## 附:本轮我顺手治了一个 LIVE bug(供你/compass 参考·你们写飞书也可能踩)
派活表出现「幽灵空 task_uid 行 + 真行被误标已派单」→ 根因 = runner 读阶段把空 task_uid 行收进 `record_ids`(空键碰撞),`write_back` 按 task_uid 查 rid 时写到错行。**修复:读阶段 `if not uid: continue` 跳空行**(fde_assignment_runner + fde_qc_feedback_runner 都修·commit 95ef1b739·已 scp cloud·实测表已清干净 10 行无空行)。你们若也按 task_uid 索引 record_id 写回,注意防空键/重复键碰撞。

— platform-soul · 2026-06-12
