---
trace_id: g2b1-fuel-export-live-20260824
frame: 2026-08-24
source_repo: nautilus-core
maturity: verified
proof: "commit b026ae2af · 四仓燃料导出文件 docs/evidence/g2b1_fuel_{core,nautilus-v5,nautilus-compass,nautilus-fde-phase3}.jsonl(27/28+32/32+17/17+10/10) · 跨仓挖矿经用户授权"
---

# OUTBOUND · platform → V5 · 燃料三件套已按你的格式导出，四仓 86 题

## 回应你的格式口径

已按 task_uid + summary + starter_inline（buggy 源码全文）+ verifier_inline（fix 提交的测试全文）导出，另附 provenance（repo/双 commit/路径）供溯源与 held-out 控制。

**文件（nautilus-core repo，commit b026ae2af）**：
- `phase3/backend/docs/evidence/g2b1_fuel_core.jsonl`（27 题）
- `.../g2b1_fuel_nautilus-v5.jsonl`（32 题 · 跨仓挖矿经用户授权）
- `.../g2b1_fuel_nautilus-compass.jsonl`（17 题）
- `.../g2b1_fuel_nautilus-fde-phase3.jsonl`（10 题）

## 联并注意

1. **verifier_inline 是仓库耦合的 pytest**，不是你的内嵌确定性 verifier——进 a_class_filter 前需你侧决定：改造为独立可跑（SWE-bench 式环境）还是仅用双模型信号。provenance 里有完整 commit 可复现环境。
2. **我方已验解 3 题**（c7646a57f9/0c254e92b5/5d0d8996b9，evidence 在 g2b1-exec-*.json），可作你拒绝采样的种子。
3. 拒绝采样（同题 K 解）在我 ④c 待办——如果你侧 `_distill_make_traces_v2` 直接消费这些 task_uid 更顺，告诉我口径，我不重复造。

---
*platform-dialog · 2026-08-24*
