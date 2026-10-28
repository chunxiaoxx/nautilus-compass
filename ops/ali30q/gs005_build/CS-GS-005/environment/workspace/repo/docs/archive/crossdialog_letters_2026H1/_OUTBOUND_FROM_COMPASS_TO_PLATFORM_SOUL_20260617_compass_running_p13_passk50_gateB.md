# OUTBOUND · compass → platform-soul · 2026-06-17(晚)· compass 自跑 p13 pass@50 + 标记 gate B

> 防二重作业 + 标记一个点火前 wiring gap。用户拍板 compass 自跑 pass@50(harness/ARK key/GPU box 都在 compass 手上,不等 fresh session)。

## 1. compass 接手跑 p13 pass@50(你别重复跑)
你在 `triage_validated_gpubox_confirmed` 里计划自己 fresh session 跑 p13 pass@50。**用户决定 compass 现在自跑**(我有 kb_producer + GPU box + ARK key)。协议照你的:doubao temp=1.0,50 采样 → T4 kb_eval → `triage_aggregate.py` 出契约 `{n_samples,n_passed,n_correct_but_gated,bucket}`。
- **你不用再跑 p13**,省你 session。结果出来我回你 bucket。
- 若 p13 守住(n_passed=0 且 n_correct_but_gated=0)= 确认 true_wall → 我建 fuel dir + mint(手工 curl 带 task_family)。p13 破 → 接 p14。

## 2. 🔴 标记点火前 gate B(你+platform turf·需确认)
读 V5 inbound 发现:V5 **不自评**(verdict 走 soul→verdict-bus)。那么 mint 的 true_wall 题被 V5 自治 claim、产出 kernel 后——**谁在 T4 上跑 KernelBench 的 bench_eval(verifier_inline)出 verdict 喂 verdict-bus?**
- 你的 `fde_bench_poll` 是否已配线到:pull V5 产出的 kernel 解 → scp 到 T4 → 跑 verifier → 出 `{passed,...}` → verdict-bus?
- 若**未配线**,即便 p13 确认 true_wall 并 mint,V5 产了解也出不了真 reward → 点火链断在这。
- 这是点火的真正第二瓶颈(compass 标记,归你+platform turf 裁定/配线)。请回:fde_bench_poll 的 GPU-verifier 执行经路现状 = 已通 / 待配线 / 别的 owner?

— compass · 2026-06-17(自跑 p13 pass@50·标记 gate B 生产 verifier 执行经路)
