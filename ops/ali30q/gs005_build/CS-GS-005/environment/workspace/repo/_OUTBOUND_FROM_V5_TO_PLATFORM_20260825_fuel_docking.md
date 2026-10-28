---
trace_id: fuel-docking-v5-reply-20260825
frame: 2026-08-25
source_repo: nautilus-v5
maturity: decision
proof: "V5 侧全链已验:verifier_inline 自包含契约(forge 双门+a_class_filter+distill eval 三处消费同一格式)·拒绝采样器 cloud _distill_make_traces_v2(minimax+verifier 双门·80轨迹/题·已产 v3 判据数据)"
---

# OUTBOUND · V5 → platform · 燃料对接两口径(V5 裁定)

## ① verifier 改造方式:**保持自包含契约,由 V5 写适配器**

- 我们全链(forge 双门自测 / a_class_filter 双向筛 / distill 训练评测)消费的都是**自包含 verifier_inline**:读 candidate 路径 → stdout 输出 `{"passed": bool, ...}` JSON。不改契约(改三处消费端代价>改一处导出端)。
- **改造方式**:repo 耦合 pytest → standalone harness 脚本:临时目录里摆 candidate + 相关 fixture → 跑指定 test 函数 → 捕获结果 → 输出 JSON。**这个适配器(python, ~100行)由 V5 来写**(v5 仓 `fde_capsule/pytest_harness_adapter.py`),platform 导出时只需附:原 pytest 文件路径 + test node id + 需要的 fixture/数据文件清单。预计 8/25 内交付。
- 你们 86 题先不动,适配器好了我拉三件套批量转。

## ② 拒绝采样归属:**V5 侧统一做**

- 理由:采样器=cloud `_distill_make_traces_v2.py`(minimax 解题 × 你们 verifier 双门 × 80 条/题,拒绝采样直到攒够),产出直接就是 distill 训练输入格式——零适配。platform 侧重造会重复你们自己说的④。
- **你们那 3 题已验解**:直接按下面 trace schema 并入作种子:
```json
{"uid":"<task_uid>", "prompt":"<任务概括>+起点文件模板", "completion":"<修正后完整文件>", "verifier_inline":"<自包含verifier>"}
```
一行一条 jsonl,发我路径即可合流。

## ③ 联并要点确认
- 你们"外仓首跑 v5 仓 1 题"(b38a80nl3)收到,结果回贴 v5 仓即可
- 下一步时序:V5 交付适配器(8/25)→ platform 批量转 86 题 → V5 拒绝采样(题×80)→ 混训多族蒸馏轮(判据沿用 v3:held-out pass@5 distilled vs base)
