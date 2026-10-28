# 🔧 服务器SSH连接修复指南

**问题**: SSH端口24860无法从外部连接
**解决方案**: 通过腾讯云控制台修复

---

## 📋 修复步骤

### 第1步：检查SSH服务状态

在腾讯云控制台终端中执行：

```bash
# 检查SSH服务状态
sudo systemctl status sshd

# 检查SSH监听端口
sudo netstat -tlnp | grep ssh
```

**预期结果**: 应该看到SSH在监听22和/或24860端口

---

### 第2步：检查防火墙规则

```bash
# 检查UFW防火墙状态
sudo ufw status

# 如果防火墙开启，添加SSH端口
sudo ufw allow 24860/tcp
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 5432/tcp
sudo ufw allow 6379/tcp

# 重新加载防火墙
sudo ufw reload
```

---

### 第3步：检查SSH配置

```bash
# 查看SSH配置
sudo cat /etc/ssh/sshd_config | grep Port

# 如果没有24860端口，添加它
sudo nano /etc/ssh/sshd_config
```

**在配置文件中添加或确认**:
```
Port 22
Port 24860
```

**保存并退出**: Ctrl+X, Y, Enter

---

### 第4步：重启SSH服务

```bash
# 重启SSH服务
sudo systemctl restart sshd

# 验证SSH服务运行正常
sudo systemctl status sshd

# 再次检查监听端口
sudo ss -tlnp | grep ssh
```

---

### 第5步：验证系统资源

```bash
# 查看CPU
lscpu | grep "CPU(s):"

# 查看内存
free -h

# 查看磁盘
df -h /
```

**预期结果**:
- CPU: 4核
- 内存: 8GB
- 磁盘: 120GB

---

### 第6步：扩展文件系统（重要！）

```bash
# 扩展分区
sudo growpart /dev/vda 2

# 扩展文件系统
sudo resize2fs /dev/vda2

# 验证磁盘空间
df -h /
```

**预期结果**: 磁盘应该从59GB扩展到约118GB

---

### 第7步：检查Docker服务

```bash
# 检查Docker状态
sudo systemctl status docker

# 如果Docker未运行，启动它
sudo systemctl start docker

# 查看容器状态
docker ps -a
```

---

### 第8步：启动Nautilus服务

```bash
# 进入项目目录
cd /opt/nautilus

# 启动所有服务
docker compose -f docker-compose.simple.yml up -d

# 等待30秒
sleep 30

# 检查容器状态
docker ps
```

**预期结果**: 应该看到3个容器运行：
- nautilus-api
- nautilus-postgres
- nautilus-redis

---

### 第9步：验证服务

```bash
# 测试API
curl http://localhost:8000/

# 测试健康检查
curl http://localhost:8000/health

# 查看API日志
docker logs nautilus-api --tail=50
```

---

## 🎯 快速修复脚本

如果你想一键执行所有修复，复制以下脚本：

```bash
#!/bin/bash
echo "=== 开始修复 ==="

# 1. 配置防火墙
echo "1. 配置防火墙..."
sudo ufw allow 24860/tcp
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw reload

# 2. 重启SSH
echo "2. 重启SSH服务..."
sudo systemctl restart sshd

# 3. 扩展文件系统
echo "3. 扩展文件系统..."
sudo growpart /dev/vda 2
sudo resize2fs /dev/vda2

# 4. 启动Docker
echo "4. 启动Docker服务..."
sudo systemctl start docker

# 5. 启动Nautilus
echo "5. 启动Nautilus服务..."
cd /opt/nautilus
docker compose -f docker-compose.simple.yml up -d

# 6. 等待服务启动
echo "6. 等待服务启动..."
sleep 30

# 7. 验证
echo "7. 验证服务状态..."
echo ""
echo "=== 系统资源 ==="
free -h
df -h /
echo ""
echo "=== Docker容器 ==="
docker ps
echo ""
echo "=== SSH端口 ==="
sudo ss -tlnp | grep ssh
echo ""
echo "=== 修复完成 ==="
```

---

## 📝 执行建议

### 方案A: 逐步执行（推荐）
按照上面的步骤1-9逐步执行，这样可以看到每一步的结果。

### 方案B: 一键修复
复制快速修复脚本，保存为文件并执行：

```bash
# 创建脚本
nano /tmp/fix.sh

# 粘贴上面的脚本内容
# 保存: Ctrl+X, Y, Enter

# 添加执行权限
chmod +x /tmp/fix.sh

# 执行
sudo /tmp/fix.sh
```

---

## ✅ 验证清单

完成后检查：

- [ ] SSH服务运行正常
- [ ] 端口24860监听
- [ ] 防火墙允许SSH端口
- [ ] 文件系统已扩展到118GB
- [ ] Docker服务运行
- [ ] 3个容器都在运行
- [ ] API响应正常

---

## 🚨 如果仍然无法连接

### 检查腾讯云安全组

1. 登录腾讯云控制台
2. 进入"云服务器" → "安全组"
3. 检查入站规则是否包含：
   - TCP 22
   - TCP 24860
   - TCP 8000
4. 如果没有，添加这些规则

---

**创建时间**: 2026-02-28 02:25
**优先级**: 🔥 高
**预计时间**: 5-10分钟

**请按照步骤执行，完成后告诉我结果！** 🚀
