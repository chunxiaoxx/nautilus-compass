# cloud 嵌入切 Mac mini · 内网穿透方案对比(2026-10-16 · R543)

> 目标:cloud 服务器(UVM-0-8-ubuntu,腾讯云)的 compass-bge-daemon 嵌入从"本地 CPU fallback"切到 Mac mini 的 bge-m3 服务(8400)。
> 前提:Mac mini 在家庭局域网(192.168.5.x),无公网 IP;cloud 在公网。

## 候选方案对比

| 方案 | 原理 | 延迟 | 安全暴露面 | 稳定性 | 复杂度 | 判 |
|---|---|---|---|---|---|---|
| **A. cloud→Mac 反向隧道(reverse SSH)** | Mac mini 主动向 cloud 建一条 `ssh -R 19988:127.0.0.1:8400` 隧道(出方向,免公网暴露);cloud daemon 的 EMBED_PROXY 指 `127.0.0.1:19988` | +0(隧道内,Mac→cloud 同城/公网一次往返) | **零新增暴露**(cloud 只听 127.0.0.1;Mac 出方向连接) | 依赖 Mac 在线+家庭网络;断线自动重连(AutoSSH) | 低(一条 AutoSSH 命令+launchd) | ✅ **推荐** |
| B. Tailscale mesh | 两机装 Tailscale 虚拟组网,cloud 直连 Mac mini 的 100.x 地址 | +5-20ms(magic 网络直连或中继) | 零公网暴露,设备级加密 | 极稳(WireGuard) | 中(两机装客户端+账号) | 备选(引入第三方依赖) |
| C. frp 公网穿透 | Mac mini 跑 frpc,公网 VPS 跑 frps,暴露 8400 | +20-50ms | **新增公网暴露面**(需 token 鉴权,有被扫风险) | 中 | 中 | ❌ 违背最小暴露原则 |
| D. cloud 直连家庭宽带(DDNS+端口转发) | 路由器端口转发 8400 | +20ms | **高危**(家庭 IP 直曝+服务公网可达) | 差(家宽 IP 漂移) | 低 | ❌ 否决 |
| E. 维持 CPU fallback | 不切 | 0.3s/条 | 零 | 稳 | 零 | 现状(cloud 记忆量小,暂可接受) |

## 判定:方案 A(reverse SSH + AutoSSH)

**理由**:零新增公网暴露、Mac mini 出方向连接(无需路由器配置)、复用既有 SSH 密钥体系(id_ed25519 已双向部署)、断线自愈成熟(AutoSSH 是标准件)。

## 实施步骤(Mac mini 侧)

### 1. AutoSSH 反向隧道(LaunchD 常驻)

```bash
# Mac mini 上:brew install autossh(或用 ssh 自带 ExitOnForwardFailure+循环)
cat > ~/Library/LaunchAgents/com.nautilus.bge-reverse-tunnel.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.nautilus.bge-reverse-tunnel</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/ssh</string>
    <string>-N</string><string>-R</string>
    <string>19988:127.0.0.1:8400</string>
    <string>-o</string><string>ServerAliveInterval=20</string>
    <string>-o</string><string>ServerAliveCountMax=6</string>
    <string>-o</string><string>ExitOnForwardFailure=yes</string>
    <string>-o</string><string>StrictHostKeyChecking=accept-new</string>
    <string>-i</string><string>/Users/<USER>/.ssh/id_ed25519</string>
    <string>ubuntu@UVM-0-8-ubuntu-ip</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
PLIST
launchctl load ~/Library/LaunchAgents/com.nautilus.bge-reverse-tunnel.plist
```

### 2. cloud 侧前置(一次性)

- Mac mini 公钥上 cloud authorized_keys(反向连接的认证;Mac mini 生成自己的 key);
- cloud 侧 sshd 确认 `GatewayPorts`(默认 no → 19988 只绑 127.0.0.1 = **正好**,零暴露);
- cloud daemon 的 EMBED_PROXY 改 `http://127.0.0.1:19988`(drop-in 一行)→ 重启 compass-bge-daemon。

### 3. 验证

```bash
# cloud 上:
curl -s http://127.0.0.1:19988/health   # 期望 Mac mini BGE 响应
# 然后 recall 实测(cloud daemon, 走 Mac mini 嵌入)
```

## 安全要点

- 反向隧道只绑 cloud 的 **127.0.0.1**(GatewayPorts=no 默认)——公网零暴露;
- Mac mini 侧是**出方向**连接(家庭网络无需任何端口转发);
- 隧道断→AutoSSH/KeepAlive 自动重连;Mac mini 离线→cloud daemon 自动 fallback CPU(既有机制);
- 钥匙:Mac mini 独立 key(不复用 A100 key)。

## 风险与回滚

- Mac mini 关机/睡眠 → 隧道断 → cloud daemon **自动 fallback CPU**(既有机制,零人为干预);
- 睡眠注意:Mac mini 需设"防止自动睡眠"(pmset)或接电源常开;
- 回滚:卸载 LaunchD + cloud EMBED_PROXY 还原 + 重启 daemon,2 分钟。

—— compass · R543 · 2026-10-16 · 方案 A 候用户确认后实施
