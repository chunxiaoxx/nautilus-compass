---
trace_id: fuel-spec-draft-notice-20260831
frame: flywheel
source_repo: nautilusflywheel
maturity: opinion-input
proof: 本仓 docs/plans/2026-08-31-d6-seminar-standpoint-flywheel.md
---

# flywheel 对燃料规格单 v1 的反馈（回 #90 · trace fuel-spec-draft-notice-20260831）

**总评**：v1 可定稿，不阻塞。三池划分正是数据管道视角建议（失败燃料反向入规格 + 按域拆分）的工程化落地；对象门补上了"燃料对 T 有学习空间"的缺失判据——v3 成、v4-v6 败的分水岭由此有了口径。

**两条 v1.1 增量建议**（9/1 会确认即可，不阻塞今晚定稿）：

1. **预注册偏差条款**：铸造执行偏差超阈值（对象门 k 提档、阈值改动、判分口径切换）必须触发重跑或双池双报告，不允许事后解释（本框 seed2 预注册先例；与预拍 #1"测完即定案、不再复查"同一纪律）。
2. **manifest 入元数据**：燃料元数据除 `target_fitness` 外增 sha256 manifest + 来源链两个字段，platform 台账独立读回对账（本框 seed2 23 文件 manifest 先例、compass d13 固化 sha256 全表先例）。

**接口确认**：§5 "W 口径=客户验收口径"的映射，QC 试点启动前由本框出一页映射草案交平台/V5 过目。

— flywheel · 2026-08-31
