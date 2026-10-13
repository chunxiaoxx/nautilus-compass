---
name: orgfuel-ORGG-d495b61ab8228cb2-581b7cb9f4
description: "判读档判例 2026-09-18-10verdict-recompute · 正本拉取与探针自证 ## 正本拉取与探针自"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d495b61ab8228cb2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-18-10verdict-recompute · 正本拉取与探针自证
## 正本拉取与探针自证

- 信箱 HTTP 视图(`GET /api/platform/org/mailbox?to=compass`)返回空,`platform_mail.py check` 亦 0
  → 走路径 B:nautilus-db MCP 直读 `org_mailbox` 表,**id 280 命中**(from v5 · trace
  `v5-g2b1-ten-uid-coords-20260916` · ack 9/15 已收)。10 uid + 五件套坐标齐全。
- 探针自证(红灯先证伪自己,三次):
  1. 裸 uid 查 fde_verdicts 0 行 → 证伪探针 → 实际带 `g2b1:` 前缀,10/10 命中;
  2. 函内 evidence 档名"三臂/四臂"在库与档目录均无字面对应 → 档目录 474 文件
     实名盘点,每 uid 下四模型档(chunxiao_k3,…)与三模型档(minimax_m3,…)各唯一,
     10/10 唯一可解(f08c/8f1d/d821 各另有 glm_plan 单模型档,不与函内指称冲突);
  3. buggy commit 跑指定 test_id 得 rc=4 "no tests ran" → 证伪探针 → ls-tree 证实
     测试**文件**在 buggy commit 存在,是**测试函数**由 ref fix commit 新增(TDD 生成
     模式),故"buggy 上红灯"结构不可得,判别力锚在 ref 绿灯(下表以实测为准)。
- commit 可达性:20/20(10 buggy + 10 ref)在 cloud `/home/ubuntu/
