# 🔧 服务器升级后连接故障排查

**问题**: SSH连接超时
**服务器**: 43.160.239.61
**升级配置**: 4核8GB 120GB

---

## 🚨 当前问题

```
ssh cloud -p 24860
ssh: connect to host 43.160.239.61 port 24860: Connection timed out
```

---

## 🔍 可能的原因

### 1. 安全组规则未配置
升级后可能需要重新配置安全组规则

### 2. SSH端口改变
升级可能重置了SSH端口到默认的22

### 3. 防火墙规则
系统防火墙可能阻止了连接

### 4. 服务器未完全启动
刚升级完成，服务可能还在初始化

---

## ✅ 解决方案

### 方案1: 检查阿里云控制台

1. **登录阿里云控制台**
   - https://ecs.console.aliyun.com

2. **检查实例状态**
   - 确认实例状态为"运行中"
   - 查看公网IP是否改变

3. **检查安全组规则**
   - 进入"网络与安全" → "安全组"
   - 确认入方向规则包含：
     - SSH: 端口22或24860
     - HTTP: 端口8000
     - PostgreSQL: 端口5432
     - Redis: 端口6379

4. **添加安全组规则**（如果缺失）
   ```
   协议类型: 自定义TCP
   端口范围: 24860/24860
   授权对象: 0.0.0.0/0
   描述: SSH访问
   ```

5. **使用VNC连接**
   - 在控制台点击"远程连接"
   - 选择"VNC连接"
   - 无需SSH即可访问

---

### 方案2: 通过VNC修复SSH

如果能通过VNC连接，执行以下命令：

```bash
# 1. 检查SSH服务状态
sudo systemctl status sshd

# 2. 重启SSH服务
sudo systemctl restart sshd

# 3. 检查SSH端口
sudo netstat -tlnp | grep ssh

# 4. 检查防火墙
sudo ufw status

# 5. 如果防火墙开启，允许SSH
sudo ufw allow 24860/tcp
sudo ufw allow 22/tcp
```

---

### 方案3: 重新配置SSH端口

通过VNC连接后：

```bash
# 1. 编辑SSH配置
sudo nano /etc/ssh/sshd_config

# 2. 确认或添加端口配置
Port 24860

# 3. 重启SSH
sudo systemctl restart sshd

# 4. 检查端口监听
sudo ss -tlnp | grep 24860
```

---

### 方案4: 检查网络配置

```bash
# 1. 检查网络接口
ip addr show

# 2. 检查路由
ip route show

# 3. 测试网络连通性
ping -c 4 8.8.8.8
```

---

## 📋 立即操作步骤

### 第1步: 阿里云控制台检查

1. 登录控制台
2. 找到实例 43.160.239.61
3. 检查状态和IP
4. 检查安全组规则

### 第2步: 使用VNC连接

1. 点击"远程连接"
2. 选择"VNC连接"
3. 输入VNC密码（如果有）
4. 进入系统

###第3步: 检查SSH服务

```bash
# 在VNC中执行
sudo systemctl status sshd
sudo netstat -tlnp | grep ssh
```

### 第4步: 修复SSH（如果需要）

```bash
# 重启SSH服务
sudo systemctl restart sshd

# 检查防火墙
sudo ufw status

# 允许SSH端口
sudo ufw allow 24860/tcp
```

###第5步: 测试连接

从本地测试：
```bash
ssh cloud -p 24860
```

---

## 🎯 快速修复命令（VNC中执行）

```bash
# 一键修复脚本
sudo systemctl restart sshd && \
sudo ufw allow 24860/tcp && \
sudo ufw allow 22/tcp && \
sudo ufw allow 8000/tcp && \
sudo netstat -tlnp | grep -E '(ssh|8000)'
```

---

## 📞 如果仍然无法连接

### 检查清单
- [ ] 实例状态为"运行中"
- [ ] 公网IP正确
- [ ] 安全组规则包含SSH端口
- [ ] SSH服务运行正常
- [ ] 防火墙允许SSH端口
- [ ] 网络连接正常

### 备用方案
1. 使用阿里云工单支持
2. 重启实例
3. 创建快照后重装系统

---

## 💡 预防措施

升级后应该做的：
1. ✅ 立即测试SSH连接
2. ✅ 检查安全组规则
3. ✅ 验证所有服务端口
4. ✅ 创建系统快照

---

**创建时间**: 2026-02-28 01:55
**状态**: 🔴 SSH连接故障
**优先级**: 🔥 高

**请按照上述步骤排查并修复！**
