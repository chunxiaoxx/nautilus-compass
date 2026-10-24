# 配置真相表(2026-10-23 盘点)

| 类 | 项 | 位置 | 版本化 | 状态 |
|---|---|---|---|---|
| launchd | ai.nautilus.bge-embed | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | ai.nautilus.frame-worker-flywheel | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | ai.nautilus.nas-backup | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | ai.nautilus.pg-tunnel-15432 | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | ai.nautilus.v5-api | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | ai.nautilus.v5-brain-tel | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | ai.nautilus.v5-brain | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | ai.nautilus.v5-rsi-daily | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | ai.nautilus.v5-rsi-guard | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | com.nautilus.bge-rerank | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | com.nautilus.bge-rerank | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | com.nautilus.bge-reverse-tunnel | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | com.nautilus.bge-reverse-tunnel | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | com.nautilus.compass-daemon | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | com.nautilus.compass-daemon | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | com.nautilus.compass-loop | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| launchd | com.nautilus.compass-loop | ~/Library/LaunchAgents/ | ❌ 不在仓 | runctl load 即生效 |
| MCP | nautilus-compass(全局 http→cloud) | ~/.claude.json | ❌ 不在仓 | 项目名已修 macOS 编码 |
| MCP | v5 bridge(stdio→cloud 9877) | nautilus-v5/.mcp.json | ✓ 已提交 0293e5cc | 9877 隧道本机 |
| MCP | core(http nautilus.social/mcp) | nautilus-core/.mcp.json | ✓ 在仓 | ⚠️ 端点 404 平台侧 |
| daemon | daemon 9876+配置注入 | 插件 .cache/daemon_env | ❌ 不在仓 | 嵌入8400/rerank8401 已配 |
| daemon | BGE 嵌入 8400 | ai.nautilus.bge-embed.plist | ❌ 不在仓 | MPS 本机 |
| daemon | rerank 8401 | com.nautilus.bge-rerank.plist | ❌ 不在仓 | token 在 ~/bge-embed/ |
| hooks | 全局 settings.json hooks | ~/.claude/settings.json | ❌ 不在仓 | 路径全验 ✓;Stop hook 1 处 Windows 残留 |
| 隧道 | cloud 反向 19988 / 9877 正向 | ssh -f -N 进程 | ❌ 不在仓 | ⚠️ 无 launchd,重启即丢! |
| launchd | com.nautilus.ali30q-loop | ops/ali30q/ | ✓脚本在仓 | 阿里判分矩阵每小时轮,渠道自适应 |
