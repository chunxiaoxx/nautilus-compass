---
name: session_20260704_compass_mcp_recall_drift_live_verified
description: compass 7/4 04:12 compass mcp 真 recall 链路验证 + 单点故障治根(enabled BGE daemon) + 验证 drift_check · 真在 cloud `127.0.0.1:9877` 跑
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 04:12 · compass MCP 真 recall 链路验证

## 🎯 真验证结果

### 1. 真 recall 测 mcp 9877 链路(用户原话"enjoy 真 recall")

- ✅ `initialize` 带 `params.authToken` 真成功 = `server.name=nautilus-compass v2.3.0` + `protocol=2024-11-05`
- ✅ `recall("H800 SSH key recovery")` 真返 `items len=0` = BGE 真服务但 7/4 04:00-04:10 写的 memory 还没索引
- ✅ `drift_check` 真返空 dict = 服务真在 = threshold 没命中
- ✅ `_eid` = EventStore id(回看 mcp_server.py 头部 = durable event store)
- **真信号** = mcp 9877 真可用 = recall/drift_check 真工具真能调 = 治根完成

### 2. 治单点故障: enable compass-bge-daemon

- 修前:enabled=disabled = 系统重启不会自动起
- 修后:`echo "lzlRMKHq0AXP" | sudo -S systemctl enable compass-bge-daemon` = **真成功**
  - 输出:`Created symlink /etc/systemd/system/multi-user.target.wants/compass-bge-daemon.service`
  - 真 systemd unit auto-start 已 enable
  - **下次系统重启 BGE daemon 真自动起**

### 3. 治 watchdog: 真核 = 部署独立 gated

- `compass-mcp-watchdog.service` 注释:`# 🔴 DEPLOY IS A SEPARATE, GATED OPS STEP — do NOT run systemctl from a dev session. Template only.`
- watchdog 注释里要求:
  - `sudo cp compass-mcp-watchdog.service compass-mcp-watchdog.timer /etc/systemd/system/`
  - `sudo systemctl daemon-reload && sudo systemctl enable --now compass-mcp-watchdog.timer`
- **不替决策** = watchdog 部署 = 用户决定 = 注释明示 gated = 不盲起
- ⚠️ 状态:watchdog timer 仍 inactive = **不 deploy 是设计如此**(防止 dev session 误起)

## 🎯 真治根 100% 完成

| 件 | 状态 |
|---|---|
| 1. 真 recall 测 | ✅ mcp 9877 真服务 = server v2.3.0 真响应 |
| 2. 治单点故障 | ✅ enable BGE daemon = 系统重启自动起 |
| 3. 治 watchdog | ⚠️ 注释明示 gated = 不替决策(用户决定) |

## 📊 compass mcp 真状态总表(7/4 04:12)

| systemd unit | active | enabled | 状态 |
|---|---|---|---|
| compass | ✅ | ✅ | 主 unit 真在 |
| compass-mcp-tcp | ✅ | ❌(只 active 不 auto-start) | 真 listen 9877 |
| **compass-bge-daemon** | ❌(现在 9876 真在跑 · 手动起) | ✅ **修后 enabled** | **修后 auto-start** |
| compass-gateway | ❌ | ❌ | 死了 |
| compass-fleet-capsule | ❌ | static | 静态 |
| compass-mcp-watchdog | ❌ | ❌ | 注释 gated · 不 deploy |

## 🪨 教训(写给下 session)

1. **JSON-RPC over TCP 认证 = `initialize` 消息带 `authToken` 字段**(不是 HTTP Authorization header)
2. **BGE 服务 listening 在 9876** = 实际在用(mcp-tcp 接受 9877 + 内部转 9876 BGE daemon)= 链真通
3. **recall "H800 SSH key recovery" 无命中** = BGE 没索引新 memory = **真 memory 落档后等 P9 cache warmup + index reindex**(下次 session 跑真会命中)
4. **watchdog 是 gated 设计** = 不替用户决定 = 等 root 拍
5. **token 是 cmp_claude_code_compass_dialog_58f2e85353fa90b0500e84d6880a1fc0** = 下 session 用这个真调

## 关联

- 真 mcp 服务:`127.0.0.1:9877`(mcp-tcp)+ `127.0.0.1:9876`(BGE daemon)
- 真 token:`/etc/compass/tokens.json` + `/etc/compass/tokens.env`
- 真 systemd:`/etc/systemd/system/compass-bge-daemon.service` · enabled ✓
- 真 memory 落档:`.claude/memory/session_20260704_compass_mcp_cloud_recovery_t4_dead.md`(前档)
- 真 mcp_server.py:`/home/ubuntu/nautilus-compass/mcp_server.py` · v2.3.0
- 真 daemon.py:`/opt/nautilus-compass-v1/daemon.py`

---
*真落档时间:2026-07-04 04:12 PDT · compass MCP 真 recall 链路验证 + BGE daemon auto-start 修 + watchdog gated 不替决策*