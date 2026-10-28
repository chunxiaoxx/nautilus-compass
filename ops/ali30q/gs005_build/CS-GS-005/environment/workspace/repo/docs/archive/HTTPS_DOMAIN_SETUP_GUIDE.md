# 🔒 Nautilus HTTPS 和域名配置指南

**日期**: 2026-02-21
**域名**: nautilus.ai (待注册)
**服务器**: 43.160.239.61

---

## 📋 当前状态

### ✅ 已完成
1. ✅ Vite配置文件创建 (端口3000)
2. ✅ 前端服务运行在3000端口
3. ✅ Nginx配置文件创建
4. ✅ 配置文件已上传到服务器

### 📍 服务端口
- **前端**: http://43.160.239.61:3000 (Vite)
- **API**: http://43.160.239.61:8000 (FastAPI)
- **WebSocket**: http://43.160.239.61:8000/socket.io

---

## 🌐 域名配置计划

### 域名结构
- **主域名**: nautilus.ai (前端)
- **www**: www.nautilus.ai (前端)
- **API**: api.nautilus.ai (后端API)

### DNS 解析配置
注册 nautilus.ai 后，需要添加以下 DNS 记录：

```
类型    主机记录    记录值              TTL
A       @          43.160.239.61       600
A       www        43.160.239.61       600
A       api        43.160.239.61       600
```

---

## 🔧 部署步骤

### 步骤 1: 域名注册和解析
1. 注册 nautilus.ai 域名
2. 在域名管理面板添加上述 DNS 记录
3. 等待 DNS 解析生效 (通常5-30分钟)
4. 验证解析：`ping nautilus.ai`

### 步骤 2: 启用 Nginx 配置
```bash
# SSH 登录服务器
ssh cloud

# 创建软链接启用配置
sudo ln -s /etc/nginx/sites-available/nautilus /etc/nginx/sites-enabled/

# 测试配置（会报错因为证书还不存在，这是正常的）
sudo nginx -t

# 暂时注释掉 SSL 配置以便先获取证书
sudo nano /etc/nginx/sites-available/nautilus
# 注释掉所有 HTTPS server 块，只保留 HTTP 块

# 重新加载 Nginx
sudo systemctl reload nginx
```

### 步骤 3: 获取 SSL 证书
```bash
# 安装 certbot（如果未安装）
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# 获取证书（域名解析生效后）
sudo certbot certonly --nginx -d nautilus.ai -d www.nautilus.ai -d api.nautilus.ai

# 按提示输入邮箱地址
# 同意服务条款
# 证书将保存在 /etc/letsencrypt/live/nautilus.ai/
```

### 步骤 4: 启用完整 Nginx 配置
```bash
# 取消注释 HTTPS 配置
sudo nano /etc/nginx/sites-available/nautilus
# 取消所有 HTTPS server 块的注释

# 测试配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

### 步骤 5: 验证 HTTPS
```bash
# 测试 HTTPS 访问
curl -I https://nautilus.ai
curl -I https://api.nautilus.ai

# 检查证书
sudo certbot certificates
```

---

## 📝 Nginx 配置说明

### HTTP 配置 (端口 80)
- 用于 Let's Encrypt 证书验证
- 自动重定向到 HTTPS

### HTTPS 前端 (nautilus.ai)
- 监听 443 端口
- 反向代理到 localhost:3000 (Vite)
- 支持 WebSocket 升级
- 自动添加安全头

### HTTPS API (api.nautilus.ai)
- 监听 443 端口
- 反向代理到 localhost:8000 (FastAPI)
- 支持 WebSocket (socket.io)
- CORS 头由 FastAPI 处理

---

## 🔒 SSL 证书自动续期

### 配置自动续期
```bash
# Certbot 会自动配置 cron 任务
# 查看续期任务
sudo systemctl status certbot.timer

# 手动测试续期
sudo certbot renew --dry-run

# 如果测试成功，证书会在到期前自动续期
```

---

## 🔍 故障排查

### 问题 1: DNS 解析未生效
```bash
# 检查 DNS 解析
nslookup nautilus.ai
dig nautilus.ai

# 如果未解析，等待更长时间或检查 DNS 配置
```

### 问题 2: Certbot 获取证书失败
```bash
# 确保 80 端口可访问
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 确保 Nginx 正在运行
sudo systemctl status nginx

# 检查域名是否正确解析到服务器
curl -I http://nautilus.ai
```

### 问题 3: HTTPS 无法访问
```bash
# 检查证书文件是否存在
sudo ls -la /etc/letsencrypt/live/nautilus.ai/

# 检查 Nginx 错误日志
sudo tail -50 /var/log/nginx/error.log

# 测试 Nginx 配置
sudo nginx -t
```

### 问题 4: WebSocket 连接失败
```bash
# 确保 Nginx 配置包含 WebSocket 支持
# 检查 Upgrade 和 Connection 头设置

# 测试 WebSocket 连接
wscat -c wss://api.nautilus.ai/socket.io/
```

---

## 📊 当前配置文件

### Vite 配置 (vite.config.ts)
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0'
  }
})
```

### Nginx 配置位置
- **配置文件**: /etc/nginx/sites-available/nautilus
- **软链接**: /etc/nginx/sites-enabled/nautilus
- **本地备份**: C:\Users\chunx\Projects\nautilus-core\nginx-nautilus.conf

---

## 🚀 部署后验证清单

### 域名访问
- [ ] https://nautilus.ai 可访问
- [ ] https://www.nautilus.ai 可访问
- [ ] https://api.nautilus.ai 可访问
- [ ] http://nautilus.ai 自动重定向到 HTTPS

### 功能验证
- [ ] 前端页面正常显示
- [ ] API 接口正常响应
- [ ] WebSocket 连接正常
- [ ] SSL 证书有效（绿色锁图标）

### 性能验证
- [ ] 页面加载速度 < 2秒
- [ ] API 响应时间 < 100ms
- [ ] SSL 握手时间 < 500ms

---

## 📞 快速命令参考

### 查看服务状态
```bash
# 前端服务
ps aux | grep vite

# 后端服务
ps aux | grep uvicorn

# Nginx 状态
sudo systemctl status nginx

# 证书状态
sudo certbot certificates
```

### 重启服务
```bash
# 重启前端
sudo pkill -f 'vite'
cd /home/ubuntu/nautilus-mvp/phase3/frontend
nohup npm run dev > ~/vite-3000.log 2>&1 &

# 重启 Nginx
sudo systemctl reload nginx

# 重启后端（如需要）
sudo systemctl restart nautilus-backend
```

### 查看日志
```bash
# 前端日志
tail -f ~/vite-3000.log

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# SSL 证书日志
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

---

## 🎯 下一步行动

### 立即可做
1. ✅ Vite 已配置为 3000 端口
2. ✅ Nginx 配置文件已创建
3. ⏳ 等待域名注册

### 域名注册后
1. 配置 DNS 解析
2. 等待解析生效
3. 启用 Nginx 配置
4. 获取 SSL 证书
5. 启用 HTTPS

### 验证和优化
1. 测试所有功能
2. 配置 CDN（可选）
3. 配置监控告警
4. 性能优化

---

## 💡 额外建议

### 安全加固
```bash
# 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 配置 fail2ban（防止暴力破解）
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

### 性能优化
```nginx
# 在 Nginx 配置中添加缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 启用 gzip 压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

### 监控配置
```bash
# 安装监控工具
sudo apt install htop iotop nethogs -y

# 配置日志轮转
sudo nano /etc/logrotate.d/nginx
```

---

**文档版本**: 1.0
**创建日期**: 2026-02-21
**状态**: 等待域名注册

**Nautilus · 智涌 - 智能如潮，螺旋向上！** 🚀
