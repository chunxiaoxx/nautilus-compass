# Compass Cursor Extension

> v0.9.0-dev · cross-agent memory + drift detection in Cursor IDE.
>
> Pairs with: Claude Desktop · Cline · OpenClaw · Hermes · Nautilus agents · 任何 MCP/A2A 兼容 client.

## What

5 commands accessible via Command Palette (Ctrl+Shift+P):

| Command | What |
|---|---|
| **Compass: Recall Memory** | Cross-agent semantic recall (BGE-m3) |
| **Compass: Drift Timeline** | ASCII drift history · last 30d |
| **Compass: Write Observation** | Manual obs write · drift self-audit |
| **Compass: Show My Profile** | Cross-agent profile aggregate |
| **Compass: Start MCP Server** | (auto on activation) |

Status bar shows current drift state (green/yellow/red).

## Why

```
Cursor 自带 MCP support (~/.cursor/mcp.json)
但 user 要手动配置 + 调用要走 chat (@compass.recall)

本扩展提供:
  · 一键安装 · 不用改 mcp.json
  · Command Palette 直接调 (不打字 @ 也能用)
  · Status bar drift 警告 (实时看 AI 是否漂)
  · 跨其他 client 共享 memory (相同 user_id)
```

## Install (planned · 2026-09)

```bash
# VS Code marketplace
code --install-extension nautilus.compass-cursor
# 或 cursor
cursor --install-extension nautilus.compass-cursor
```

Or build from source:

```bash
cd cursor-extension
npm install
npm run compile
npx vsce package
# install the .vsix
```

## Config (in Cursor settings)

```json
{
  "compass.userId": "u_yourname",
  "compass.agentType": "cursor",
  "compass.baseUrl": "https://compass.nautilus.social",
  "compass.autoIngestOnSave": false
}
```

## Status

- ✅ Scaffold (本文件 · src/extension.ts · package.json · tsconfig)
- 🟡 真编译 (需要 npm install + tsc)
- 🟡 marketplace 上架
- 🟡 Auto-ingest on save (实验)
- 🟡 Profile UI (现在是 raw JSON · 后续做 Webview)

## Roadmap

| Phase | Item |
|---|---|
| v0.9.3 | npm publish + marketplace 上架 |
| v0.9.4 | Webview profile 可视化 |
| v0.9.5 | Drift status bar 实时联动 (websocket) |
| v1.0 | E2EE 客户端加密 (libsodium-wrappers) |
| v1.0.1 | 集成 Nautilus marketplace agent recommendation |

## Related

- Main Python package: `nautilus-compass` (pip)
- npm wrapper: `@nautilus/compass-mcp`
- Other clients: Claude Desktop · Cline · 自家 agent (via SDK)

```
Same COMPASS_USER_ID across all → memory federation 自动生效
```
