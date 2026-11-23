# Nautilus Compass 3.4.0 发布规划

状态：准备阶段

本计划只定义发布边界、证据和执行顺序，不改变当前版本号，不创建 tag，不发布 PyPI、MCP Registry 或插件包。

## 发布目标

3.4.0 的目标是把 Compass 从“记忆服务升级”收敛为“可验证的跨 agent 连续性基础设施”。

本版核心能力包括：

1. 项目级 Context Capsule。
2. Hash-bound Protected Cognition Vault。
3. 9B 本地值守和受限工具运行时。
4. Evidence Capsule、Handoff Capsule 和 Consumer Receipt 的接口约定。
5. 重排超时保护和可观测 fallback。
6. 迁移、交接和记忆晋级的明确状态边界。

## 当前版本事实

| 位置 | 当前读数 | 发布前动作 |
| --- | --- | --- |
| `pyproject.toml` | 3.3.0 | 对齐到候选版本 |
| `package.json` | 3.3.0 | 对齐到候选版本 |
| `.claude-plugin/plugin.json` | 3.3.0 | 对齐到候选版本 |
| `.registry/server.json` | 3.2.0 | 对齐并确认 registry 包坐标 |
| `server.json` | 3.1.1 | 对齐并核对 transport 与 tools 描述 |
| git latest tag | v3.3.0 | RC 前创建 `v3.4.0-rc1` |
| 当前 Compass 分支 | 本地领先 origin，工作树有运行时状态文件 | 发布前建立干净 release worktree |

版本元数据存在漂移。完成统一前不发布。

## 发布范围

### 纳入 3.4.0

#### 连续性绑定

- `tools/context_capsule.py`
- 项目、任务、线程和工作树绑定
- 受保护认知金库路径和哈希
- 分支、HEAD、daemon ping 和 AGENTS hash 记录
- 胶囊失效后的 `not_computable`

#### 认知金库

- Core 侧 `core_cognition_vault_v1.json`
- registry hash 校验
- Context Card 先读金库的读取顺序
- critical 负证据和晋级边界保护

#### 本地 9B 运行时

- 本地 Qwen3.5-9B route
- 重复工具计划保护
- 只读任务写入硬闸
- 工具预算耗尽后的结论收尾
- external model 和 external send 双零回执

#### Recall 稳定性

- 远端重排超时后的 dense fallback
- timeout cooldown
- local CPU fallback 只保留给契约或模型错误
- rerank backend、fallback 和 latency 可读

### 不纳入 3.4.0 的内容

- 9B 新权重训练和自动晋级
- 未经独立验证的历史候选自动发布
- 组织级 MCP projection 的全部修复
- Flywheel 未取得权威 manifest 的训练链
- CodeSense 尚未取得用户审核的平台提交
- 客户验收、商业收入或外部 benchmark 新成绩

这些内容可以在后续版本形成单独 release gate。

## 发布前必须完成的工程工作

### R0 版本和来源统一

- 统一 `pyproject.toml`、`package.json`、`.claude-plugin/plugin.json`、`server.json` 和 `.registry/server.json` 的版本语义。
- 明确哪个文件是源码版本正本，哪个文件是发布镜像。
- 生成版本一致性测试。
- 生成 release manifest，包含 commit、tag、包文件哈希和 MCP metadata 哈希。

### R1 契约和测试

- 运行 Context Capsule 测试。
- 运行核心认知金库生成和 stale hash 测试。
- 运行 9B local-agent 测试。
- 运行 daemon rerank remote、timeout 和 production fallback 测试。
- 运行全量 pytest、ruff、wheel build 和 fresh virtualenv import smoke。

### R2 安装和升级

- 从空目录安装 wheel。
- 验证 `nautilus_compass`、`nautilus_compass.sdk`、`nautilus_compass.assay`、`gep` 可导入。
- 验证 `nautilus-compass`、`compass-mcp`、`compass-a2a` CLI 可运行。
- 验证旧项目 memory 文件不被自动改写。
- 验证旧配置缺少认知金库时能明确返回 pending 或 not_computable。

### R3 本地生产 canary

- 备份当前 daemon、launchd plist、memory manifest 和 9B route。
- 用 RC1 在独立 worktree 运行 Context Capsule、Vault、Recall、9B loop。
- 运行至少一轮真实本地值守。
- 读取 consumer receipt。
- 观察 rerank timeout、cooldown、fallback 和 recall latency。
- 任一关键回执缺失，停止进入 GA。

### R4 发布一致性

- `python -m build --wheel --sdist`。
- 检查 wheel 内容和包版本。
- 运行 `scripts/release_notes_extract.py --version 3.4.0`。
- 生成 GitHub release draft。
- 生成 MCP registry 更新草稿。
- 逐项核对 PyPI、GitHub、MCP registry、README 和 plugin metadata。

## 发布门槛

### 必须通过

- 版本元数据一致。
- 关键测试全绿。
- fresh install 可导入和启动。
- Context Capsule 能生成和验证。
- vault hash 变化能阻断动作。
- 本地 9B route 有回执。
- external model 使用为 0。
- external send 为 0。
- Recall 失败和 fallback 有明确状态。
- release manifest 和 rollback 包存在。

### 必须保持公开的限制

- 长期记忆有效性仍需消费者回放证明。
- 9B 还不是训练完成模型。
- 本版不承诺客户验收和商业闭环。
- 本版不把历史 benchmark 记录升级为新实测。

## 回滚方案

触发任一条件时回滚：

- 版本或包坐标不一致。
- 安装后关键 import 失败。
- daemon 使用了错误源码或错误模型。
- vault 校验失效但动作仍继续。
- recall 延迟异常且 cooldown 没有生效。
- 外部发送或自动晋级边界被绕过。

回滚顺序：停止新 launchd、恢复 daemon 和 plist、恢复 release manifest 记录的配置、重新运行协议级 ping 和 authenticated recall、读取 consumer receipt。历史 memory 文件保持原样。

## RC1 验收卡

```text
release_version: 3.4.0-rc1
source_head: pending
wheel_sha256: pending
sdist_sha256: pending
registry_metadata_sha256: pending
vault_schema: codesense-core-cognition-vault/1
context_capsule_test: pending
9b_runtime_test: pending
rerank_timeout_test: pending
fresh_install_import: pending
local_canary: pending
consumer_readback: pending
external_send: false
customer_acceptance: not_assessed
rollback_bundle: pending
```

## 3.4.0 GA 后续版本建议

### 3.4.1

- 处理 RC1 中的安装、metadata 和跨环境问题。
- 补齐 Platform、Flywheel、V5 的 capsule adapter。

### 3.5.0

- 引入消费者回放和长期记忆有效性基线。
- 支持 32/8/8 gold、validation、test 的 NACRE 入口。
- 增加跨对话迁移 canary。

### 4.0.0

- 在独立 verifier、训练 holdout 和回滚门通过后，讨论验证经验进入创新模型的原生机制。

## 当前下一动作

1. 修订并统一五处版本元数据。
2. 在独立 release worktree 生成 RC1，而不触碰当前共享工作树。
3. 先跑 full test、wheel、fresh install 和本地 canary。
4. 生成发布草稿和对外变更说明，等待用户审核。
5. 用户审核前不打 tag、不 push、不发布、不对外发送。
