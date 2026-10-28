# OpenClaw 云端配置

## 架构

```
本地电脑 ──SSH隧道──> 云端OpenClaw:18789
```

**重要**：SSH隧道必须由本地电脑运行，不是云端！

## 检查状态

```bash
# 云端：检查OpenClaw
systemctl --user status openclaw-gateway

# 云端：检查端口
sudo lsof -i :18789

# 本地：检查SSH隧道
netstat -an | grep 18789
```

## 如果出问题

```bash
# 1. 停止systemd服务
systemctl --user stop openclaw-gateway
systemctl --user disable openclaw-gateway

# 2. 清理PM2
pm2 delete all

# 3. 重启
systemctl --user enable openclaw-gateway
systemctl --user start openclaw-gateway
```
