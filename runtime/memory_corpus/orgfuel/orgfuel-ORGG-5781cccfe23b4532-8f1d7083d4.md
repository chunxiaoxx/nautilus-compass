---
name: orgfuel-ORGG-5781cccfe23b4532-8f1d7083d4
description: "判读档判例 2026-09-07-compass架构审计-七算子框架与三修复方案 · 2. 三修复方案（按杠杆排序） #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5781cccfe23b4532
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-07-compass架构审计-七算子框架与三修复方案 · 2. 三修复方案（按杠杆排序）
## 2. 三修复方案（按杠杆排序）

### 修复一：fact_status 写入 gate（评估前移，最轻）

- 变更：memory frontmatter 增加字段 `fact_status: measured | inferred | heard`（实测过/推断/传闻）+可选 `verified_at`（上次实测日期）
- 纪律：写入方（Claude/用户）落条目时必填；recall 注入时随条目带出——高 stakes 决策（部署/对外/杀进程）只采信 measured 级
- 实施位置：记忆写入模板（全局 CLAUDE.md 记忆节+memory 文件约定）；daemon 侧注入格式（涉及 recall 输出模板，实施前先读 recall.py 确认注入拼装点）
- 验证：抽样 10 条新记忆检查字段存在+一次 high-stakes 提问只命中 measured

### 修复二：写入查重触发合并（给合并装触发器）

- 机制：新 memory 写入前先 BGE 查重（对既有条目集），cosine ≥0.9 命中→进入合并流程（升级覆盖原条目，保持单 SSOT）而非新建；0.75-0.9 灰区→提示人工裁决并回填 [[链接]]
- 实施位置：session_writer/记忆写入路径前置钩子（实施前核对 session_writer.py 与 daemon 的写入入口；仓内已有 cycle_consolidator.py/ssot_consistency.py，先读其既有职责避免重复造轮子——本仓反复教训）
- 验证：故意写一条与既有条目高度相似的记忆，确认走合并而非新增；MEMORY.md 索引行数不增

### 修复三：召回沿链一跳（组合
