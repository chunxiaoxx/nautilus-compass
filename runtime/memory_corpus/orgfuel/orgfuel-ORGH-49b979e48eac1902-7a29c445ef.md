---
name: orgfuel-ORGH-49b979e48eac1902-7a29c445ef
description: "commit b0466a5afe88 2026-06-07 feat(fde): read_buyer_tasks —"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-49b979e48eac1902
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit b0466a5afe88 2026-06-07
feat(fde): read_buyer_tasks — 飞书 Bitable 买方题 → 规范题行(turf: 读归 compass) (#47)
读归 compass(复用 feishu_client G3 读管线 · 别让平台重造 feishu)· 归一输出
键对齐 fde-row-assembler 二期 16 列契约 · 平台 /fde/dispatch + assemble_rows 可
直接消费。compass 只读 + 归一,不 POST dispatch(派归平台 · 连接器归 V7)。

- bitable_record_to_buyer_task: 官方全称/简写列名都归一 · 富文本单元格抽文本
- read_buyer_tasks: 过滤空行 · skip_dispatched 挑未派单题 · 纯数据供消费方决策
- CLI: --feishu / --input · NO LLM 纯映射
- 7 TDD 绿 + 实测真飞书 Bitable 读 6 题(task_uid→uid/level/派单状态默认)

Co-authored-by: nautilus-platform-saas-dialog <saas-dialog@nautilus.social>
