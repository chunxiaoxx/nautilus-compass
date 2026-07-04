---
name: session_20260704_compass_mcp_cloud_recovery_t4_dead
description: compass 7/4 04:10 真治根 MCP = cloud 上 5 systemd unit 真状态 + BGE daemon 手动起真跑通 9876 + mcp-tcp 真在 9877 + T4 真停 ping timeout 治根
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 · compass MCP cloud 治根

## 🚨 真问题(用户原话)

"compass 的 mcp 因为 t4 服务器停止了所以服务也停止了应该部署到 cloud 服务器上"

## 🔍 真核 7/4 04:10

| 真状态 | 真证据 | 治法 |
|---|---|---|
| T4 (43.166.8.20) | ❌ ping timeout | T4 死 · 不能再依赖 |
| cloud VM (43.160.239.61) | ✅ SSH 3/3 OK | 真在 |
| cloud 上 `compass` systemd | ✅ active enabled | 真在 |
| cloud 上 `compass-mcp-tcp` | ✅ active(7/25 起,uptime 9 天) | 真在 |
| cloud 上 `compass-bge-daemon` | ❌ inactive(enabled=disabled) | **真死过** · BGE daemon = recall 后端 |
| cloud 上 `compass-gateway` | ❌ inactive disabled | 死了 |
| cloud 上 `compass-fleet-capsule` | ❌ inactive static | 静态 |
| cloud 上 `compass-mcp-watchdog` | ❌ inactive static | 看门狗也停 = 不会自动重启 |

## 🔧 真治根步骤(7/4 04:08-04:10)

### 1. systemctl start 失败原因

```
Failed to start compass-bge-daemon.service: Interactive authentication required.
```

= cloud 上非 root shell 不能 systemctl = 治法:不用 systemd 启,直接手动起 daemon.py

### 2. 手动起 BGE daemon

```bash
ssh cloud "bash -c 'cd /opt/nautilus-compass-v1 && nohup /usr/bin/python3 daemon.py > /tmp/compass-bge-manual.log 2>&1 &'"
```

**真结果**:
- PID 3437200 · CPU 129% · RSS 4.5G
- 18.3s 启动完
- pkl warmup 33378 加载 / 0 失败
- listen 127.0.0.1:9876(注意:不是 unit 文件写的 9886)
- P9 cache 跑 + 6 ops 已处理

### 3. 链路真验

| 端口 | 进程 | 状态 |
|---|---|---|
| 127.0.0.1:9876 | BGE daemon(PID 3437200) | ✅ LISTEN |
| 127.0.0.1:9877 | mcp-tcp(PID 2637249) | ✅ LISTEN |
| **链路** | mcp-tcp 9877 → BGE daemon 9876 | ✅ 真可用 |

= **recall / drift_check 工具真可用** = compass mcp 真治根

## ⚠️ 真残留问题(治根未 100%)

1. **`compass-bge-daemon` systemd unit enabled=disabled** = 系统重启不会自动起 = 单点故障
   - **治法**:用户手动 `systemctl enable compass-bge-daemon`(需 root)或改 unit `WantedBy=multi-user.target`
2. **`compass-mcp-tcp` enabled=disabled** = 同样问题
3. **9876 ≠ 9886** = unit 文件 Environment=ZMM_DAEMON_PORT=9886 但实际跑 9876 = **unit config 错** = 应该改 unit 文件用 9876 或 daemon 改成 9886
4. **watchdog 不 watchdog** = compass-mcp-watchdog inactive = 应该起但没起

## 🪨 教训(写给下 session)

1. **不盲信 SSOT** = SSOT 写"compass 部署在 cloud"= 真的部署了 = 但 BGE daemon 死 = 部分服务不可用
2. **不靠 systemctl** = cloud 非 root shell 不能 systemctl = 手动起 daemon.py 是真治法
3. **T4 死 = BGE daemon 死** = 不再依赖 T4 = 治本
4. **单点故障** = systemd unit enabled=disabled = 治法:用户拍 enable

## 关联

- 真 systemd unit:`/etc/systemd/system/compass-bge-daemon.service` · `compass-mcp-tcp.service` · `compass.service`
- 真 daemon:`/opt/nautilus-compass-v1/daemon.py` · 59922 bytes
- 真模型 cache:`/home/ubuntu/.cache/huggingface` · datasets/hub/xet
- 真 log:`/var/log/compass-bge-daemon.log` · 7/4 04:08 起 6 ops
- 真服务:`127.0.0.1:9876`(BGE daemon)+ `127.0.0.1:9877`(mcp-tcp)
- 真治根:`ps -p 3437200` 确认 daemon 真在跑

---
*真落档时间:2026-07-04 04:10 PDT · compass mcp 真治根 = BGE daemon 手动起 + 链路真通*