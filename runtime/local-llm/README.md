# 本地 9B 路由

## 快速值守

使用 `claude-local-9b-settings.json` 将 Claude Code 的本地会话接到 Mac 上的 MLX 服务。

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:11435 \
ANTHROPIC_AUTH_TOKEN=local \
ANTHROPIC_API_KEY=local \
claude --bare \
  --settings runtime/local-llm/claude-local-9b-settings.json \
  --model sonnet \
  -p '只回复 LOCAL_CLAUDE_ROUTE_OK'
```

当前服务端的 Claude 协议默认关闭思考链，适合短答、值守和状态整理。显式传入 `thinking.type=enabled` 时才启用思考链。对应 smoke 回执为：

- `claude-local-9b-smoke-20261123.json`
- `claude-local-9b-alias-smoke-20261123.json`

## 当前边界

- 11435 的 Qwen3.5-9B-4bit 已加载。
- `thinking.type=enabled` 的响应仍需更大输出预算和结构化解析，不能直接作为正式记忆发布器。
- Claude CLI 会在 stderr 打印本地模型名未登记的提示，stdout 路由和结果仍可独立验收。
