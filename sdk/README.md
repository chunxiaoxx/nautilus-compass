# compass SDK · multi-agent ingest

让任何 agent 把交互观察 (observation) 写入 compass platform · 实现"用户跨 agent 历史融合"。

## 接入要点 (3 行代码)

```python
from compass_client import CompassClient
client = CompassClient(user_id="u_chunx", agent_id="ag_openclaw_main", agent_type="openclaw")
client.ingest_obs(name="...", description="...", body="...", drift="green")
```

## 当前可用 agent_type

| type | 说明 | 接入方式 |
|---|---|---|
| `claude-code` | Claude Code CLI | hook (已通) |
| `openclaw` | OpenClaw 战略 agent | SDK · 自家可控 |
| `hermes` | Hermes IM/agent loop | SDK · 自家可控 |
| `cursor` | Cursor IDE | extension (planned) |
| `codex` | OpenAI Agent SDK | proxy (planned) |
| `zenmind` / `nautilus` / `caishen` | 自家产品 | SDK |
| `custom` | 任何其他 | SDK |

## 接入流程 (3 步)

### 1. 注册 agent (一次性)

```python
client = CompassClient(user_id="u_chunx", agent_id="ag_openclaw_main", agent_type="openclaw")
# agent 第一次写 obs 时 server auto-create · 不需要单独 register
```

### 2. 在关键节点 ingest

**何时写 obs**:
- agent 完成一个任务 (任务级)
- session 结束 (session 级)
- 检测到 drift / 用户反馈 / 错误 (signal 级)
- 关键决策 (decision 级)

```python
client.ingest_obs(
    name="OpenClaw 战略评估完成",
    description="用户问『V5 飞轮真转吗』· OpenClaw 给出 6 维评分",
    body="...完整内容...",
    type_="decision",          # bugfix | feature | refactor | discovery | decision | change
    concept="pattern",         # gotcha | pattern | trade-off | how-it-works | why-it-exists | problem-solution | what-changed
    drift="green",             # green | yellow | red
    drift_signals=[],          # red 时填具体证据
    extra_meta={"task_id": "t_123"},  # 任意附加元数据
)
```

### 3. recall 跨 agent 历史

```python
# 默认跨所有自己 agent · 实现"懂用户"
hits = client.recall("飞轮真转吗", cross_agent=True)
# 限单个 agent
hits = client.recall("...", agent_id="ag_openclaw_main")
# 只看 red drift 的历史
hits = client.recall("...", drift="red")
```

## E2EE (端到端加密 · 用户主权)

```python
client = CompassClient(
    user_id="u_chunx",
    agent_id="ag_openclaw_main",
    encrypt_payload=True,  # 内容加密 · server 看不到
)
# meta (timestamp/drift/type) 仍明文 · server 用于索引
# content (name/description/body) AES-GCM 加密 · server 不可读
```

需安装 `compass_crypto` (libsodium 包装 · 后续提供)。

## 离线缓冲

网络断时 · obs 自动写到 `~/.compass/pending/<user>_<ts>.jsonl` · 恢复后调:

```python
client.replay_buffer()  # 回放并清空
```

## 自测

```bash
python compass_client.py --user-id u_test --name "自测一条"
# 当前 server 还没实现 /v1/observations · 会 buffer 到 ~/.compass/pending/
# server 实现后 · 调 client.replay_buffer() 自动回放
```

## 环境变量 (省去硬编码)

```bash
export COMPASS_USER_ID=u_chunx
export COMPASS_AGENT_ID=ag_openclaw_main
export COMPASS_TOKEN=<JWT after auth>      # v0.9+ 必须
```

```python
from compass_client import from_env
client = from_env(agent_type="openclaw")
```

## SDK 状态

| 版本 | 状态 | 说明 |
|---|---|---|
| 0.9 (本) | ✅ Client lib · offline buffer · 元数据 ready | 等 server `/v1/observations` |
| 1.0 | planned | E2EE · region sharding · auth · cross-agent recall |

## 安全 / 隐私默认值

- `encrypt_payload=False` 默认 (E2EE 是 v1.0 默认)
- `offline_buffer=True` 默认 (网络挂时不丢数据)
- 未设 `token` 时不发认证头 (server 拒绝写)

## 接入 OpenClaw / Hermes 示例

见 `examples/openclaw_integration.py` · `examples/hermes_integration.py`
