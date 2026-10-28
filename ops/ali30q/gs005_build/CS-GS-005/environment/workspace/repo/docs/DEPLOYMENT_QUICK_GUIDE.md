# 🚀 服务器部署快速指南

**目标**: 将最新代码部署到nautilus.social
**当前状态**: SSH不可用，需要通过控制台操作
**预计时间**: 1-2小时

---

## 📋 前置条件

### 已完成 ✅
- ✅ 代码已推送到GitHub (48547d17)
- ✅ 前端P0/P1修复完成
- ✅ 本地构建和测试通过
- ✅ 文档完整

### 需要准备
- [ ] 云服务商控制台访问权限
- [ ] 服务器Web控制台/VNC访问
- [ ] root权限

---

## 🔧 部署步骤

### Step 1: 恢复SSH连接 (15分钟)

**1.1 登录云服务商控制台**
```
访问控制台 → 找到服务器实例 → 打开Web控制台/VNC
```

**1.2 检查SSH服务**
```bash
# 检查SSH服务状态
systemctl status sshd

# 如果未运行，启动SSH
systemctl start sshd
systemctl enable sshd

# 检查SSH配置
cat /etc/ssh/sshd_config | grep Port
cat /etc/ssh/sshd_config | grep PermitRootLogin
```

**1.3 检查防火墙**
```bash
# 检查防火墙状态
ufw status

# 允许SSH端口
ufw allow 22/tcp

# 或者临时关闭防火墙测试
ufw disable
```

**1.4 检查安全组**
```
在云服务商控制台:
安全组 → 入站规则 → 确保开放TCP 22端口
```

**1.5 验证SSH连接**
```bash
# 从本地测试
ssh root@nautilus.social
```

---

### Step 2: 检查当前状态 (10分钟)

**2.1 系统状态**
```bash
# 系统信息
uptime
df -h
free -h
```

**2.2 服务状态**
```bash
# 检查Nginx
systemctl status nginx
curl http://localhost

# 检查后端API
pm2 list
pm2 logs nautilus-api --lines 20
curl http://localhost:3000/api/health
```

**2.3 代码版本**
```bash
cd /root/nautilus
git log -1 --oneline
git status
```

---

### Step 3: 部署最新代码 (30分钟)

**3.1 备份当前版本**
```bash
cd /root/nautilus
git log -1 > /tmp/pre-deploy-version.txt
pm2 save
```

**3.2 拉取最新代码**
```bash
# 拉取代码
git fetch origin
git pull origin master

# 确认版本
git log -1 --oneline
# 应该显示: 48547d17 docs: 添加部署推送完成报告和今日工作总结
```

**3.3 更新后端**
```bash
cd /root/nautilus/phase3/backend

# 安装依赖
npm install

# 重启服务
pm2 restart nautilus-api

# 检查日志
pm2 logs nautilus-api --lines 50
```

**3.4 更新前端**
```bash
cd /root/nautilus/phase3/website

# 安装依赖
npm install

# 构建前端
npm run build

# 备份旧版本
mv /var/www/nautilus /var/www/nautilus.backup.$(date +%Y%m%d_%H%M%S)

# 部署新版本
mkdir -p /var/www/nautilus
cp -r dist/* /var/www/nautilus/

# 设置权限
chown -R www-data:www-data /var/www/nautilus
chmod -R 755 /var/www/nautilus
```

**3.5 重启Nginx**
```bash
# 测试配置
nginx -t

# 重启Nginx
systemctl restart nginx
```

---

### Step 4: 验证部署 (15分钟)

**4.1 API健康检查**
```bash
# 本地检查
curl http://localhost:3000/api/health

# 应该返回: {"status":"ok"}
```

**4.2 前端检查**
```bash
# 检查前端文件
ls -lh /var/www/nautilus/

# 检查网站
curl -I https://nautilus.social

# 应该返回: HTTP/1.1 200 OK
```

**4.3 功能测试**
```bash
# 在浏览器中测试:
1. 访问 https://nautilus.social
2. 检查页面加载
3. 测试用户注册/登录
4. 测试Agent功能
5. 测试任务功能
```

**4.4 日志检查**
```bash
# 后端日志
pm2 logs nautilus-api --lines 100

# Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 系统日志
journalctl -u nginx -n 50
```

---

### Step 5: 监控和优化 (持续)
**5.1 性能监控**
```bash
# 系统资源
htop
iotop

# 服务状态
pm2 monit
```

**5.2 错误监控**
```bash
# 实时日志
pm2 logs nautilus-api --lines 0

# 错误日志
grep -i error /var/log/nginx/error.log | tail -20
```

---

## 🚨 故障排查

### 问题1: 前端页面空白

**检查**:
```bash
# 检查文件是否存在
ls -lh /var/www/nautilus/index.html

# 检查Nginx配置
cat /etc/nginx/sites-enabled/nautilus.conf

# 检查Nginx错误日志
tail -f /var/log/nginx/error.log
```

**解决**:
```bash
# 重新部署前端
cd /root/nautilus/phase3/website
npm run build
cp -r dist/* /var/www/nautilus/
systemctl restart nginx
```

### 问题2: API无响应

**检查**:
```bash
# 检查进程
pm2 list

# 检查日志
pm2 logs nautilus-api --lines 100

# 检查端口
netstat -tlnp | grep 3000
```

**解决**:
```bash
# 重启API
pm2 restart nautilus-api

# 如果失败，查看详细错误
pm2 logs nautilus-api --err --lines 200
```

### 问题3: 数据库连接失败

**检查**:
```bash
# 检查MongoDB
systemctl status mongod

# 检查Redis
systemctl status redis
redis-cli ping
```

**解决**:
```bash
# 重启数据库
systemctl restart mongod
systemctl restart redis
```

---
## ✅ 部署检查清单

### 部署前
- [ ] 代码已推送到GitHub
- [ ] 本地构建成功
- [ ] 测试全部通过
- [ ] 备份当前版本

### 部署中
- [ ] SSH连接正常
- [ ] 代码拉取成功
- [ ] 依赖安装完成
- [ ] 构建成功
- [ ] 文件复制完成

### 部署后
- [ ] API健康检查通过
- [ ] 前端页面加载正常
- [ ] 用户功能正常
- [ ] 无错误日志
- [ ] 性能正常

---

## 📊 预期结果

### 成功标志
- ✅ SSH连接恢复
- ✅ 代码版本: 48547d17
- ✅ API响应正常
- ✅ 前端加载正常
- ✅ 所有功能正常

### 关键改进
- ✅ TypeScript错误: 0个
- ✅ 构建时间: 6.40秒
- ✅ 打包大小: 436.86 KB
- ✅ 测试覆盖: 149个测试

---

## 📞 需要帮助？

如果遇到问题，检查以下文档：
- `docs/DEPLOYMENT_PUSH_COMPLETE.md` - 部署状态报告
- `docs/WORK_SUMMARY_2026-03-12.md` - 今日工作总结
- `docs/FRONTEND_FIX_COMPLETE.md` - 前端修复详情
- `phase3/website/FRONTEND_P0_P1_FIX_SUMMARY.md` - 详细修复报告

---

## 🎯 快速命令参考

```bash
# 一键部署脚本 (在恢复SSH后使用)
cd /root/nautilus && \
git pull origin master && \
cd phase3/backend && npm install && pm2 restart nautilus-api && \
cd ../website && npm install && npm run build && \
cp -r dist/* /var/www/nautilus/ && \
systemctl restart nginx && \
echo "部署完成！"

# 验证部署
curl http://localhost:3000/api/health && \
curl -I https://nautilus.social && \
pm2 logs nautilus-api --lines 20
```

---

**创建时间**: 2026-03-12 00:45
**目标版本**: 48547d17
**预计时间**: 1-2小时
**优先级**: 🔴 高
