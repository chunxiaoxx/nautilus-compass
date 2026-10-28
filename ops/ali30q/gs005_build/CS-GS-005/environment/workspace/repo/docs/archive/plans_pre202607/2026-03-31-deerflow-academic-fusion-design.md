# DeerFlow × Academic Tasks 深度融合设计

**日期**: 2026-03-31
**状态**: 设计草案

---

## 1. 现状

### DeerFlow 当前调用方式

`services/deep_research.py` 实现了忠实于 DeerFlow v1 的 5 节点管道：

```
Coordinator → Background Investigator → Planner → Research Team (并行) → Reporter
```

- 通过 `POST /api/research/deep` 直接调用（与 academic_tasks 系统独立）
- 返回结构化 `sections`（summary / findings / recommendations）+ `observations_count`
- 无 NAU token 发放，无 agent 信用分更新，无 Basescan 记录

### Academic Tasks 当前执行流程

1. `POST /academic_tasks` → 创建 DB 记录 → `asyncio.create_task(_dispatch_academic_task)`
2. `_dispatch_academic_task` → `AcademicTaskService.execute_task()`
3. `_is_research_task()` 关键词检测 → 已路由至 `_execute_research_pipeline()`（调用 DeerFlow）
4. 任务完成 → 更新 survival scores → **mint NAU**（`NautilusTokenService.mint_task_reward`）→ Basescan 留 tx_hash

**已有桥接**：`_is_research_task` + `_execute_research_pipeline` 已实现基础路由，但 DeerFlow 返回结果映射粗糙，NAU 奖励使用默认值 1，`pipeline: "deerflow"` 字段未写入 DB。

---

## 2. 融合方案

### 2.1 任务路由规则

| task_type | 执行路径 | 说明 |
|-----------|---------|------|
| `research` (新增) | DeerFlow `thorough` | 明确研究综述类 |
| `general_computation` + 描述含 ≥2 研究关键词 | DeerFlow `standard` | 现有自动检测 |
| `statistical_analysis` + 描述含 `review/survey/compare` | DeerFlow `standard` | 统计综述任务 |
| 其余所有类型 | 现有 CodeExecutor | 数值计算任务 |

新增 `AcademicTaskType.RESEARCH = "research"` 枚举值，并在 `TASK_TYPE_REWARDS` 中添加 `"research": 8`（介于 physics_simulation 和 ml_training 之间）。

### 2.2 depth 映射

- 描述 < 100 字 → `quick`（3 步）
- 描述 100–500 字 → `standard`（4 步）
- 描述 > 500 字或含 `comprehensive/systematic/meta-analysis` → `thorough`（后台执行）

---

## 3. 数据流设计

```
DeerFlow pipeline.run() 返回:
  {
    report,        → academic_task.result (output 字段)
    sections,      → academic_task.parameters["_deerflow_sections"]
    sub_questions, → academic_task.parameters["_deerflow_steps"]
    observations_count,
    duration_seconds,
    job_id,
  }

映射到现有 result 结构:
  {
    "code": None,
    "output": sections["summary"] + "\n\n" + sections["findings"],
    "plots": None,
    "error": None,
    "execution_time": duration_seconds,
    "validation": {"passed": True, "warnings": []},
    "pipeline": "deerflow",
    "sections": sections,           # 结构化输出
    "quality_score": 0.85,
    "quality_level": "GOOD",
  }
```

`sections` 写入 DB `parameters` JSON 的 `_deerflow` 命名空间，不影响现有字段。

---

## 4. NAU 分配（多 agent 协作）

当前单 agent 完成，未来 OpenClaw agent 提交任务时，DeerFlow 内部有 N 个 Researcher 并行工作。

**MVP 方案**（单钱包，简单）：全额 NAU 发给提交任务的 agent 钱包，`task_type="research"` 固定奖励 8 NAU。

**Phase 2 方案**（多钱包协作，链上分配）：

```
总奖励 = 8 NAU (research) 或按 steps 数量动态：4 + steps * 1

分配：
  Coordinator agent wallet  → 40% (协调者)
  每个 Researcher wallet    → 60% / N (平均分配给 N 个研究者)
```

需要 `ResearchState` 记录各 node 的 agent_wallet，`_reporter_node` 完成后批量 mint。Phase 2 实施时扩展 `ResearchState` 数据类即可，当前 DB schema 无需变更。

---

## 5. MVP 实施步骤

**Step 1** — 添加 `research` task_type 枚举 + NAU 奖励映射
文件：`api/academic_tasks.py`（枚举），`services/nautilus_token.py`（奖励表）

**Step 2** — 完善 `_execute_research_pipeline`：depth 自动映射 + sections 写入 DB parameters
文件：`services/academic_task_service.py`

**Step 3** — 前端 AgentSurvivalPage 新增 `research` 任务类型选项，展示 `sections` 结构化输出
文件：`phase3/website/src/pages/AgentSurvivalPage.tsx`

**Step 4** — OpenClaw agent 注册后，用真实钱包地址提交一个 `research` 任务，验证：
`academic_task.blockchain_tx_hash` 非空 + Basescan 可查 NAU mint 记录

**Step 5** — 集成测试：mock DeerFlow pipeline，验证 DB 字段映射、NAU mint 调用参数

---

## 关键约束

- DeerFlow 为同进程调用，`thorough` 深度任务需走 `BackgroundTasks`（已有机制）
- NAU mint 为非阻塞，失败不影响任务状态（现有设计保留）
- `_is_research_task` 现有关键词检测保留作为兜底，新 `research` 枚举优先匹配
