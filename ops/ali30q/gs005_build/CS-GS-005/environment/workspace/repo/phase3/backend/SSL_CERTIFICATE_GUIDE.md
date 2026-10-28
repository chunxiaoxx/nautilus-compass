# 🔐 SSL证书配置指南

**配置时间**: 2024-03-08 07:35
**难度**: 中等
**预计时间**: 1小时

---

## 📋 SSL证书选项

### 选项1: Let's Encrypt（推荐）✅

**优点**:
- 免费
- 自动续期
- 受信任的CA
- 简单易用

**步骤**:

#### 1. 安装Certbot
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx -y
```

#### 2. 获取证书
```bash
# 停止占用80端口的服务
sudo systemctl stop nginx

# 获取证书
sudo certbot certonly --standalone \
  -d nautilus.example.com \
  -d www.nautilus.example.com \
  --email admin@nautilus.example.com \
  --agree-tos \
  --non-interactive

# 证书位置
# /etc/letsencrypt/live/nautilus.example.com/fullchain.pem
# /etc/letsencrypt/live/nautilus.example.com/privkey.pem
```

#### 3. 配置自动续期
```bash
# 测试续期
sudo certbot renew --dry-run

# 添加定时任务
sudo crontab -e
# 添加: 0 0 * * * certbot renew --quiet
```

#### 4. 更新配置
```bash
# .env.production
SSL_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/nautilus.example.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/nautilus.example.com/privkey.pem
```

---

### 选项2: 自签名证书（仅测试）⚠️

**警告**: 仅用于开发/测试环境

```bash
# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nautilus.key \
  -out /etc/ssl/certs/nautilus.crt \
  -subj "/C=US/ST=State/L=City/O=Nautilus/CN=nautilus.example.com"

# 设置权限
sudo chmod 600 /etc/ssl/private/nautilus.key
sudo chmod 644 /etc/ssl/certs/nautilus.crt
```

---

### 选项3: 商业证书

**购买证书**:
1. 从CA购买（DigiCert, Comodo等）
2. 生成CSR
3. 提交验证
4. 下载证书
5. 安装证书

---

## 🔧 Nginx配置

### 创建Nginx配置文件

```nginx
# /etc/nginx/sites-available/nautilus
server {
    listen 80;
    server_name nautilus.example.com www.nautilus.example.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name nautilus.example.com www.nautilus.example.com;

    # SSL证书
    ssl_certificate /etc/letsencrypt/live/nautilus.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nautilus.example.com/privkey.pem;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 安全头
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 代理到Backend
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件
    location /static {
        alias /var/www/nautilus/static;
        expires 30d;
    }
}
```

### 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/nautilus /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

---

## 🔍 验证SSL

### 1. 浏览器测试
```
访问: https://nautilus.example.com
检查: 绿色锁图标
```

### 2. 命令行测试
```bash
# 检查证书
openssl s_client -connect nautilus.example.com:443 -servername nautilus.example.com

# 检查SSL评分
curl -I https://nautilus.example.com
```

### 3. 在线工具
```
SSL Labs: https://www.ssllabs.com/ssltest/
检查评分应该是A或A+
```

---

## 📊 SSL配置清单

### 部署前
- [ ] 域名DNS已配置
- [ ] 80端口可访问
- [ ] 443端口开放
- [ ] Certbot已安装

### 获取证书
- [ ] 证书获取成功
- [ ] 证书文件存在
- [ ] 权限设置正确
- [ ] 自动续期配置

### Nginx配置
- [ ] 配置文件创建
- [ ] HTTP重定向HTTPS
- [ ] SSL参数正确
- [ ] 安全头配置
- [ ] 代理配置正确

### 验证
- [ ] HTTPS可访问
- [ ] 证书有效
- [ ] SSL评分A+
- [ ] 自动续期测试

---

## 🚨 常见问题

### 问题1: 证书获取失败
```bash
# 检查DNS
nslookup nautilus.example.com

# 检查80端口
sudo netstat -tlnp | grep :80

# 查看日志
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### 问题2: Nginx启动失败
```bash
# 检查配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 检查证书路径
ls -la /etc/letsencrypt/live/nautilus.example.com/
```

### 问题3: 证书过期
```bash
# 手动续期
sudo certbot renew

# 检查证书有效期
openssl x509 -in /etc/letsencrypt/live/nautilus.example.com/fullchain.pem -noout -dates
```

---

## 📝 快速命令

```bash
# 一键配置（Let's Encrypt）
sudo certbot certonly --standalone \
  -d nautilus.example.com \
  -d www.nautilus.example.com \
  --email admin@nautilus.example.com \
  --agree-tos --non-interactive

# 更新.env.production
echo "SSL_CERT_PATH=/etc/letsencrypt/live/nautilus.example.com/fullchain.pem" >> .env.production
echo "SSL_KEY_PATH=/etc/letsencrypt/live/nautilus.example.com/privkey.pem" >> .env.production

# 重启服务
sudo systemctl restart nginx
docker-compose -f docker-compose.production.yml restart
```

---

**配置人**: Dialog A
**状态**: ✅ 指南完成

---

# 🔐 SSL证书配置指南完成！
# ✅ 推荐使用Let's Encrypt！
# 🎯 预计1小时完成配置！
