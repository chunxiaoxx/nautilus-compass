# 核心认知金库规范 V1

## 目的

解决 CodeSense 和其他组织 agent 在上下文切换后反复丢失关键认知的问题。

核心认知金库保存最重要的事实、负证据、任务边界和晋级规则。它保存的是带来源和哈希的保护性投影，不复制业务正本，也不替代各仓库的状态文件。

## 为什么需要金库

1M 上下文只能增加一次调用能看到的内容，不能保证下一次调用继续看到同一批内容。

模型上下文还会受到以下因素影响：

- 每次会话实际读取的文件不同
- 历史摘要会丢失负结果和边界
- 语义召回按相似度排序，重要性不等于相似度
- 新旧状态可能同时存在
- 模型会优先处理当前提示，忽略较早的任务规则
- 平台回执和本地文件可能没有绑定到同一任务身份

因此，核心认知必须有固定入口、固定身份、固定哈希和固定读取顺序。

## 金库内容

每条保护事实至少包含：

```text
entry_id
criticality
source_path
source_selector
source_sha256
project_scope
task_id
fact_status
observed_at
valid_until
negative_evidence
promotion_boundary
```

最少保护四类内容：

### 身份

- 当前 agent 角色
- 当前项目
- 当前任务和子任务
- 当前工作树和 owner
- 当前允许的外部动作

### 负证据

- reward 缺失
- customer acceptance 未观察到
- training episode 为 0
- 平台提交未成功
- 认证、权限、模型渠道或消费者回读缺失

### 晋级边界

- local_ready 不等于 formal_candidate
- platform eval 不等于 task-submit
- task-submit 不等于 customer acceptance
- 文件存在不等于语义连续性
- recall 命中不等于记忆有效

### 下一动作

- owner
- 判据
- 证据坐标
- 剩余问题
- 下一件可执行工作

## 保护规则

1. 金库只接受来源绑定的投影。
2. 来源哈希变化时，旧投影自动失效，不能静默继续使用。
3. 关键事实只能由当前任务正本更新。
4. 普通会话摘要不能覆盖 critical 条目。
5. 历史条目可以归档，不能删除或改写成当前事实。
6. 任何晋级动作必须同时读取金库和业务正本。
7. 金库状态为 `not_computable` 时停止外部提交和记忆发布。

## 每个对话框的读取顺序

1. 读取金库入口。
2. 校验 registry/source hash。
3. 读取当前任务 Context Card。
4. 读取当前合同、平台回执和最新失败证据。
5. 再按查询需要召回长历史。
6. 收尾时写回 owner、判据、证据坐标、剩余问题和下一动作。

长上下文可以帮助分析，金库负责保证关键认知不会被长上下文截断或稀释。

## CodeSense 第一版落地

当前第一版已经落在 `nautilus-core/ops/ali_phase2/`：

- `core_cognition_vault_v1.json` 是生成后的 hash-bound 投影。
- `build_core_cognition_vault.py` 从当前任务 registry 重新生成投影。
- `render_context_card.py` 在 Context Card 中加入金库入口和 registry hash。
- `--check` 会在金库缺失、schema 错误或 registry hash 过期时失败。

当前金库保护的重点是 CS-507 身份、冻结样例、R190 reward 缺失、T02 kit 缺失、task-submit 边界和 customer acceptance 未观察到。

## 后续版本

### V1.1

- 将 Compass、Platform、Flywheel 的 owner 和 task id 纳入同一套 capsule 引用。
- 增加 `valid_until` 和冲突记录。
- 把关键负证据同步到每个 agent 的 handoff capsule。

### V1.2

- 将消费者 readback 加入晋级判据。
- 对“模型已经知道”增加机器可读的来源和回读要求。
- 对重要认知增加独立 verifier 签名。

### V2

- 将金库接入组织级 context capsule。
- 支持跨仓库迁移的 source manifest、release manifest 和 rollback manifest。
- 允许 9B 使用金库作为压缩和验证输入，但禁止自动改写 critical 条目。
