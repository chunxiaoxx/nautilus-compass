# Compass 产品化与工程化落地 V1

## 产品定位

Compass 提供组织 agent 的连续性基础设施。它帮助系统在切换模型、切换对话、切换平台和切换工作树后，继续使用正确的身份、任务、证据和下一动作。

Compass 的交付对象不是一批摘要文件，而是一组可以校验、回放和消费的连续性对象。

## 产品边界

### Context Capsule

绑定 actor、project、task、thread、checkout、权限和 live probe。

当前入口：

```bash
python tools/context_capsule.py make \
  --task-id <task> \
  --thread-id <thread> \
  --vault <core-cognition-vault.json> \
  --require-vault \
  --output <capsule.json>

python tools/context_capsule.py validate \
  --capsule <capsule.json> \
  --require-vault
```

校验状态使用 `agree` 和 `not_computable`。分支、工作树、daemon 或核心认知金库哈希变化时，胶囊失效并要求重新生成。

### Protected Cognition Vault

保存关键身份、负证据、晋级边界和下一动作的 hash-bound 投影。

业务正本保留在各职责仓库。金库只保存指针、哈希、关键事实和读取规则。普通语义记忆不能覆盖 critical 条目。

当前 CodeSense 入口：

- Core `ops/ali_phase2/core_cognition_vault_v1.json`
- Core `ops/ali_phase2/build_core_cognition_vault.py`
- Core `ops/ali_phase2/render_context_card.py`
- Compass `docs/roadmap/CORE_COGNITION_VAULT_SPEC_V1_20261123.md`

### Evidence Capsule

记录输入、版本、配置、输出、失败和哈希。它让本地完成、服务运行、平台交付和客户接受保持分开。

### Handoff Capsule

记录主线、边界、剩余问题、证据坐标和下一动作。它是跨 agent 和跨对话的最小交接单元。

### Consumer Receipt

记录哪个消费者读取了结果、是否采用、是否拒绝、是否触发纠偏。没有消费者回读，系统只能报告可达性和生成，不报告业务有效性。

## 最小运行架构

```text
Source / Platform / Mail / GitHub
              |
              v
      Context Capsule Gate
              |
              v
    Protected Cognition Vault
              |
              v
    Compass Recall + Evidence
              |
              v
       Agent / Platform / Flywheel
              |
              v
       Consumer Receipt + Assay
```

每条链路都保留原始错误和 `not_computable`，不把 fallback、缓存命中、HTTP 200 或进程存活升级为成功。

## 工程化原则

### 单一正本

业务事实只在职责仓库中维护。Compass 保存跨系统索引和证据引用，避免复制出第二份业务状态。

### 哈希绑定

所有关键 capsule、vault、release manifest 和 VerifyPack 都绑定来源哈希。哈希变化时自动失效。

### 明确状态机

统一使用：

```text
local_ready
live_verified
delivered
platform_evaluated
task_submitted
customer_accepted
promoted
```

每个状态必须有独立证据和消费者读回。

### 可暂停和可恢复

9B 压缩、独立验证和记忆晋级均采用有限批次。失败保留，重试次数有限，关键异常自动停止晋级。

### 默认拒绝外发和晋级

外部发送、记忆发布、任务提交、模型晋级和部署都需要当前授权、来源绑定和对应回执。

## 产品版本路线

### V1 内部连续性产品

目标是让四个主仓和 Codex/Claude 对话都能使用同一套 capsule 和 vault 协议。

验收项：

- 每个 CodeSense 任务生成并校验 Context Capsule
- 关键负证据进入 Protected Cognition Vault
- 切换工作树或分支时 capsule 自动失效
- 当前任务没有 project/task scope 时停止平台动作

### V1.1 组织协同产品

- Platform、Flywheel、V5 生成同样格式的 Handoff Capsule
- 统一 Consumer Receipt
- 统一跨仓库 release manifest
- 统一失败 corpus 和迁移 canary

### V2 外部验证产品

- VerifyPack 和签名回执成为外部合作交付物
- 提供独立复算、负结果、判据和回滚信息
- 通过权限隔离支持多项目和多组织
- 以任务错误减少、交接时间和复算成本作为价值指标

## P0 现在执行的工作

1. 将 CodeSense Context Card 的金库校验接入所有本地预检入口。
2. 将 Compass Recall 先读 critical vault，再读普通语义记忆。
3. 为 R192、Flywheel p1-3 和 V5 主线各生成一个任务级 capsule。
4. 让所有关键交接携带 vault id、source hash 和 consumer receipt 状态。
5. 通过回放确认金库确实减少 CodeSense 的重复丢失，而不是只增加文件数量。

## 主要成功指标

- 任务身份串线率为 0
- 核心负证据丢失率为 0
- capsule 哈希失效后继续执行的次数为 0
- 平台状态误报率持续下降
- 关键记忆消费者回读覆盖率达到 100%
- 记忆回放能够降低已知错误复发率
- 外部 VerifyPack 可以由非实现者独立复算
