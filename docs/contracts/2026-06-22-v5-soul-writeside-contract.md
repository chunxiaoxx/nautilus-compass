# 写端契约 · compass 记忆胶囊 ← V5/soul · 2026-06-22

> compass 侧定义,V5/soul 后续接(不阻塞 v2.3.0 发版)。目的:把记忆胶囊从"裸 learning 行"
> 升级为"带质量元数据 + 结构化边界"的进化胶囊。compass 实现层就绪,缺的是写端传全字段。

## W1 写端(已上线·请 V5 传全 verdict 元数据)

`compass_fleet_memory.write_learning(agent_id, task_family, reason, *, reward, bucket, score, source)`

- **现状**:函数签名已支持全部元数据(commit 历史中的 P0 防退化)。已实现晋升门(reward<1.0 拒写)。
- **请 V5 做**:解题 settle 后调用时传全字段(当前多数调用只传 `reason`+`reward`):
  - `reward`(float·已传):验证通过分,晋升门用。
  - `bucket`(str):soul verdict 的难度/类别桶(如 `kernelbench-stump`/`ale`/`swe`)。
  - `score`(float):原始评分(连续分数题如 ALE 的真分)。
  - `source`(str):产出来源 agent/benchmark,溯源用。
- soul 的 verdict 体系(`fde_bench_runner.fast1_verdict` / `swe_verdict` / `fde_triage` 的 bucket)
  **已成体系**,这些字段它已产,只需 W1 调用时带上 —— soul 几乎不用改。

## P1 预备:结构化胶囊字段(V5 产结构化经验)

`gep/capsule_schema.py::StructuredCapsule`(本次 v2.3.0 预备态)字段契约:

| 字段 | 类型 | 语义 | 谁最懂 |
|---|---|---|---|
| `learning` | str | 可复用经验正文 | V5(解题 agent) |
| `triggers` | list[str] | 何时召回此胶囊(适用条件) | V5 |
| `env_fingerprint` | str | 在什么环境验证过(py3.11/cuda 等) | V5 |
| `confidence` | float | 置信度 | V5/soul verdict |
| `when_not_to_use` | list[str] | **失败边界**(何时别用·防误用) | V5(最懂解题边界) |

- **请 V5 做**:解题后产结构化经验(尤其 `when_not_to_use` 失败边界·agent 最懂)。
- compass 侧:serving schema 支持这些字段 + recall 返回(部署 gate·v2.3.0 不做)。

## P2 预备:report 回流(B 用完回写质量分)

- 形态:agent B 用了某胶囊解题后,把成功/失败结果(reward)回写该胶囊 → 喂质量分 → 自然选择。
- compass 侧:serving 加 report 端点 + 质量分更新(部署 gate)。
- **请 V5 做**:用完回写 report(B 解题 reward 挂回所用胶囊 obs_id)。

## 边界

- 本契约是 compass 实现层就绪后的写端对接说明,**不阻塞 v2.3.0 发版**(compass 侧 schema/重排已就绪)。
- P1/P2 端到端生效 = V5 写端配合 + serving 部署(后续)。本次 v2.3.0 交"compass 侧预备态 + 本契约"。
- 复用不重造:soul verdict 已产元数据,V5 是写端,compass 是实现层。三方各司其职。
