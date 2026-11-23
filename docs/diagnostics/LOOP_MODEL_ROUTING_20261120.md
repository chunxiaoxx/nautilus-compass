# Compass loop 模型路由核对

> 核对日期：2026-11-20。本文只记录配置来源和证据，不改变当前模型配置。

## 结论

历史上的 Compass headless loop 曾只执行：

```text
/Users/chunxiao.wang/.local/bin/claude -p "$(cat runtime/loop/round_prompt.md)" --output-format text
```

plist 没有 `--model`，也没有 `ANTHROPIC_BASE_URL`、`ANTHROPIC_MODEL` 或默认模型环境变量。`launchctl print` 的环境块只显示 PATH 和系统项。

因此旧 loop 会读取 Claude 当前用户配置。配置切换没有被旧 loop 固定，造成模型漂移。2026-11-20 已将生产值守入口切换到本地 `tools/local_loop_runner.py`，当前运行不再调用 Claude CLI。

## 读到的证据

- 当前 `~/.claude/settings.json` 的模型配置指向 GLM 5.3 系列。
- 历史导入配置和多个备份曾把 `ANTHROPIC_DEFAULT_SONNET_MODEL` 设为 `MiniMax-M3[1M]`，`ANTHROPIC_DEFAULT_HAIKU_MODEL` 设为 `k3-256k`。
- 当前交互 shell 的环境是 Kimi coding 路由，模型为 `k3-256k`。这个 shell 环境不会自动注入已经退出的 launchd job。
- `runtime/loop/rounds_stderr.log` 同时出现过 `glm-5.3-flash` 和 `MiniMax-M3[1m]` 的 `unrecognized_model` 记录，证明 loop 的实际模型来源曾发生变化。
- `runtime/loop/rounds.log` 的 429 原文是 `Token Plan 用量上限`，错误码 2056。
- `com.nautilus.distill-review-worker` 的 plist 明确写了 `--reviewers minimax-m3,kimi-k3-256k`。这是蒸馏审查 worker 的双审配置，不是 headless loop 的配置。

## 429 的含义

429 来自 loop 所调用的上游 Claude 兼容接口。它表示当时所选供应商的 Token Plan 配额窗口已达到上限。它与本地 BGE-m3 daemon、9876 端口、GitHub 或 Gmail 无关。

历史轮次显示 MiniMax 路径在 429 后曾恢复，说明至少有一部分 429 是配额窗口耗尽或恢复，而不是代码异常。当前仍不能把“恢复过”当成“稳定可用”。

## 造成问题的根因

1. Loop 没有自己的模型和 provider 配置。
2. Claude 用户配置在迁移、切换中转站和切换模型时反复变化。
3. launchd job 继承的是 launchd 环境，不会继承当前终端里执行过的 `kimi` 或 `minimax` shell 函数。
4. 429 失败没有在 loop 启动前做 provider/model 预检，失败时仍会产生空轮次。

## 推荐修复

固定 `com.nautilus.compass-loop` 的模型路由，不再依赖用户配置。

建议至少固定以下四项：

- provider base URL
- API 认证变量名
- `--model` 的精确模型名
- 429、5xx 和未识别模型的 fail-closed 规则

当前有两条候选路线。

### 路线 A · Kimi K3-256K

适合长上下文值守和历史压缩。需要在 plist 中明确写入 Kimi endpoint、认证变量和 `--model k3-256k`，并先做一次无写入 smoke test。

### 路线 B · GLM 5.3 Flash

适合低成本常规值守。需要确认中转站实际接受的模型 ID。`glm-5.3-flash` 已在 stderr 出现过未识别提示，不能只改字符串后直接上线。

MiniMax M3 继续保留给已经明确声明使用它的 distill reviewer，不应作为 Compass headless loop 的隐式默认值。

## 当前状态

- [实测] 历史外部 loop 的模型路由未固定，曾同时出现 GLM 和 MiniMax 模型标识。
- [实测] 429 的错误码为 2056，文案是 Token Plan 用量上限。
- [实测] `com.nautilus.compass-loop` 已切换为 `tools/local_loop_runner.py`，不再调用 Claude CLI。
- [实测] `com.nautilus.bait-loop` 和 `com.nautilus.distill-review-worker` 已由 launchd 禁用，避免继续消耗外部模型额度。
- [实测] 本地 loop 已完成至少两轮，`external_model_used=false`，摘要模型为 `Qwen3.5-9B-4bit`。
- [实测] 本地 loop 的探针包含 11435、9876、平台信箱、Gmail、GitHub mentions 和 injection sentinel，未执行外部发帖或发信。
- [证据] 当前回执为 `runtime/loop/local_round_receipt.json`，切换备份在 `runtime/loop/maintenance_backups/20261120-local-model/`。
- [实测] `tools/local_agent_runtime.py` 已把 Qwen3.5-9B 接到白名单工具执行器，可做本地语义召回、证据门检查和本地草稿落盘。
- [实测] 本地 agent 累计记录 11 条训练事件，训练预览剔除 2 条不合格正向轨迹后为 7 train、1 validation、1 test，独立数据集校验通过。
- [实测] 运行时契约评测为工具白名单 100%、外部模型隔离 100%、外发隔离 100%、证据门 87.5%、草稿后置条件 50%、失败停手 50%。整体运行门仍未通过。
- [下一步] 先扩充人工审核 gold set，再做 NACRE 的离线 LoRA/QLoRA 对拍，期间不恢复外部值守 loop。

## 9B 本地模型核对

- [实测] `com.nautilus.local-llm` LaunchAgent 正常，监听 `127.0.0.1:11435`。
- [实测] `/health` 返回 `Qwen3.5-9B-4bit`、`loaded=true`、`thinking=true`、`max_tokens=8192`。
- [实测] `/v1/models` 返回 `Qwen3.5-9B-4bit`。
- [实测] OpenAI 兼容接口可返回文本，但在 32 token smoke test 中没有严格执行“只输出 READY”，并产生了较长分析。这说明服务可用，但还没有达到值守 loop 所需的指令服从和工具调用契约。
- [实测] `local_llm_server.py` 只实现文本生成协议，没有 Claude tool_use 或 OpenAI tool_calls 的执行器。
- [实测] `com.nautilus.compass-loop` 与 `com.nautilus.bait-loop` 都直接调用 Claude CLI，因此完全绕过 11435。
- [实测] `com.nautilus.production-loop` 当前只更新题卡和状态文件，没有调用 9B，也没有调用外部模型。

## 为什么不能直接把 11435 填进旧 plist

当前 loop 依赖 Claude CLI 来执行 shell、Gmail、GitHub、平台信箱和本地脚本。11435 目前只返回文本，不能替 Claude CLI 执行工具调用。直接把 base URL 指向 11435 会得到文本回答，工具不会自动执行，值守轮会失去实际操作能力。

正确的本地化方式是拆成两层：

1. Python 或 shell 先按固定清单执行探活和只读命令。
2. 把命令结果、错误和证据坐标交给 9B 做本地摘要、分级和下一动作建议。

待 9B 通过结构化输出、命令白名单、超时和失败回退测试后，才考虑让它生成受控动作。当前不能把它直接当成 Claude Code 的替代品。
