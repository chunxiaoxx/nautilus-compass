# Nautilus Phase 3 Backend - 生产环境安全配置指南

**版本**: 3.0.0
**日期**: 2026-02-26
**安全级别**: Production

---

## 📖 目录

1. [安全概述](#安全概述)
2. [SSL/TLS配置](#ssltls配置)
3. [防火墙规则](#防火墙规则)
4. [密钥管理](#密钥管理)
5. [访问控制](#访问控制)
6. [安全加固](#安全加固)
7. [安全监控](#安全监控)
8. [应急响应](#应急响应)

---

## 安全概述

### 安全原则

1. **最小权限原则**: 只授予必要的最小权限
2. **纵深防御**: 多层安全防护
3. **默认拒绝**: 默认拒绝所有访问，明确允许必要的访问
4. **安全审计**: 记录所有安全相关事件
5. **定期更新**: 及时更新系统和依赖包

### 安全威胁模型

**主要威胁**:
- SQL注入攻击
- XSS跨站脚本攻击
- CSRF跨站请求伪造
- DDoS拒绝服务攻击
- 暴力破解攻击
- 中间人攻击
- 私钥泄露
- 数据泄露

---

## SSL/TLS配置

### 1. 证书获取

#### 1.1 使用Let's Encrypt（推荐）

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 验证证书
sudo certbot certificates
```

**证书信息**:
- 证书路径: `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
- 私钥路径: `/etc/letsencrypt/live/yourdomain.com/privkey.pem`
- 有效期: 90天
- 自动续期: 已配置

#### 1.2 使用商业证书

```bash
# 生成CSR
openssl req -new -newkey rsa:2048 -nodes \
  -keyout yourdomain.com.key \
  -out yourdomain.com.csr

# 提交CSR到证书颁发机构
# 下载证书文件

# 安装证书
sudo cp yourdomain.com.crt /etc/ssl/certs/
sudo cp yourdomain.com.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/yourdomain.com.key
```

### 2. SSL/TLS最佳实践

#### 2.1 Nginx SSL配置

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL证书
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL协议（只允许TLS 1.2和1.3）
    ssl_protocols TLSv1.2 TLSv1.3;

    # SSL加密套件（推荐配置）
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # SSL会话缓存
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # DH参数
    ssl_dhparam /etc/nginx/dhparam.pem;
}
```

#### 2.2 生成DH参数

```bash
# 生成强DH参数（需要几分钟）
sudo openssl dhparam -out /etc/nginx/dhparam.pem 4096
```

#### 2.3 配置HSTS

```nginx
# 强制HTTPS（HSTS）
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

**HSTS预加载**:
- 访问: https://hstspreload.org/
- 提交域名到HSTS预加载列表

### 3. SSL测试和验证

#### 3.1 在线测试

```bash
# SSL Labs测试
# 访问: https://www.ssllabs.com/ssltest/
# 目标评级: A+
```

#### 3.2 本地测试

```bash
# 测试SSL连接
openssl s_client -connect yourdomain.com:443 -tls1_2

# 检查证书有效期
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# 测试HSTS
curl -I https://yourdomain.com | grep -i strict
```

### 4. 证书监控和续期

#### 4.1 自动续期

```bash
# 测试续期
sudo certbot renew --dry-run

# 查看续期定时任务
sudo systemctl status certbot.timer

# 手动续期
sudo certbot renew
```

#### 4.2 证书过期监控

```bash
# 创建监控脚本
cat > /usr/local/bin/check_ssl_expiry.sh <<'EOF'
#!/bin/bash
DOMAIN="yourdomain.com"
DAYS_WARNING=30

EXPIRY_DATE=$(echo | openssl s_client -connect $DOMAIN:443 2>/dev/null | \
  openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt $DAYS_WARNING ]; then
    echo "WARNING: SSL certificate expires in $DAYS_LEFT days"
    # 发送告警邮件
    echo "SSL certificate for $DOMAIN expires in $DAYS_LEFT days" | \
      mail -s "SSL Certificate Expiry Warning" admin@yourdomain.com
fi
EOF

chmod +x /usr/local/bin/check_ssl_expiry.sh

# 添加到cron
echo "0 0 * * * /usr/local/bin/check_ssl_expiry.sh" | crontab -
```

---

## 防火墙规则

### 1. UFW防火墙配置

#### 1.1 基本配置

```bash
# 安装UFW
sudo apt install ufw

# 默认策略（拒绝所有入站，允许所有出站）
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许SSH（修改为自定义端口更安全）
sudo ufw allow 22/tcp
# 或使用自定义端口
# sudo ufw allow 2222/tcp

# 允许HTTP和HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status verbose
```

#### 1.2 限制SSH访问

```bash
# 限制SSH连接速率（防止暴力破解）
sudo ufw limit 22/tcp

# 或只允许特定IP访问SSH
sudo ufw delete allow 22/tcp
sudo ufw allow from 192.168.1.0/24 to any port 22
```

#### 1.3 拒绝直接访问后端端口

```bash
# 确保后端端口不对外暴露
sudo ufw deny 8000/tcp
sudo ufw deny 8001/tcp

# 只允许本地访问
sudo ufw allow from 127.0.0.1 to any port 8000
```

### 2. iptables高级配置

#### 2.1 防DDoS规则

```bash
# 限制连接速率
sudo iptables -A INPUT -p tcp --dport 443 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 443 -m state --state NEW -m recent --update --seconds 60 --hitcount 20 -j DROP

# 防止SYN flood
sudo iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
sudo iptables -A INPUT -p tcp --syn -j DROP

# 防止ping flood
sudo iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT
sudo iptables -A INPUT -p icmp --icmp-type echo-request -j DROP
```

#### 2.2 保存iptables规则

```bash
# Ubuntu/Debian
sudo apt install iptables-persistent
sudo netfilter-persistent save

# CentOS/RHEL
sudo service iptables save
```

### 3. 云服务商安全组

#### 3.1 AWS安全组配置

```bash
# 入站规则
- Type: HTTPS, Protocol: TCP, Port: 443, Source: 0.0.0.0/0
- Type: HTTP, Protocol: TCP, Port: 80, Source: 0.0.0.0/0
- Type: SSH, Protocol: TCP, Port: 22, Source: YOUR_IP/32

# 出站规则
- Type: All traffic, Protocol: All, Port: All, Destination: 0.0.0.0/0
```

#### 3.2 Azure网络安全组

```bash
# 创建NSG规则
az network nsg rule create \
  --resource-group myResourceGroup \
  --nsg-name myNSG \
  --name allow-https \
  --priority 100 \
  --source-address-prefixes '*' \
  --destination-port-ranges 443 \
  --access Allow \
  --protocol Tcp
```

---

## 密钥管理

### 1. 私钥存储方式

#### 1.1 加密文件存储（推荐用于小型部署）

```bash
# 生成加密密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))" > encryption_key.txt

# 运行密钥设置脚本
python3 setup_key_management.py

# 配置环境变量
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=/home/nautilus/keys/encrypted_key.json
KEY_ENCRYPTION_PASSWORD=$(cat encryption_key.txt)

# 保护密钥文件
chmod 600 /home/nautilus/keys/encrypted_key.json
chmod 600 encryption_key.txt

# 安全删除明文密钥
shred -u encryption_key.txt
```

#### 1.2 AWS KMS（推荐用于AWS环境）

```bash
# 创建KMS密钥
aws kms create-key --description "Nautilus blockchain private key"

# 加密私钥
aws kms encrypt \
  --key-id alias/nautilus-key \
  --plaintext fileb://private_key.txt \
  --output text \
  --query CiphertextBlob > encrypted_key.txt

# 配置环境变量
KEY_SOURCE=aws_kms
AWS_KMS_KEY_ID=arn:aws:kms:region:account:key/key-id
AWS_REGION=us-east-1
BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED=$(cat encrypted_key.txt)

# 配置IAM权限
aws iam attach-role-policy \
  --role-name nautilus-backend-role \
  --policy-arn arn:aws:iam::aws:policy/AWSKeyManagementServicePowerUser
```

#### 1.3 Azure Key Vault（推荐用于Azure环境）

```bash
# 创建Key Vault
az keyvault create \
  --name nautilus-vault \
  --resource-group myResourceGroup \
  --location eastus

# 存储私钥
az keyvault secret set \
  --vault-name nautilus-vault \
  --name blockchain-private-key \
  --value "your-private-key"

# 配置环境变量
KEY_SOURCE=azure_key_vault
AZURE_KEY_VAULT_URL=https://nautilus-vault.vault.azure.net/
AZURE_KEY_VAULT_SECRET_NAME=blockchain-private-key

# 配置访问权限
az keyvault set-policy \
  --name nautilus-vault \
  --object-id <service-principal-id> \
  --secret-permissions get
```

#### 1.4 HashiCorp Vault（推荐用于企业环境）

```bash
# 启动Vault
vault server -dev

# 启用KV存储
vault secrets enable -path=secret kv-v2

# 存储私钥
vault kv put secret/blockchain/private-key value="your-private-key"

# 配置环境变量
KEY_SOURCE=hashicorp_vault
VAULT_ADDR=https://vault.yourdomain.com:8200
VAULT_TOKEN=your-vault-token
VAULT_SECRET_PATH=secret/blockchain/private-key

# 创建策略
vault policy write nautilus-policy - <<EOF
path "secret/data/blockchain/*" {
  capabilities = ["read"]
}
EOF
```

### 2. 密钥轮换

#### 2.1 配置密钥轮换

```bash
# 环境变量配置
KEY_ROTATION_ENABLED=true
KEY_ROTATION_DAYS=90
KEY_ROTATION_WARNING_DAYS=7
```

#### 2.2 密钥轮换流程

```bash
# 1. 生成新密钥对
# 2. 部署新密钥到密钥管理系统
# 3. 更新应用配置
# 4. 验证新密钥可用
# 5. 归档旧密钥（保留30天）
# 6. 更新区块链账户（如需要）
```

### 3. 密钥访问审计

```bash
# 记录所有密钥访问
# 日志位置: /var/log/nautilus/key_access.log

# 监控异常访问
tail -f /var/log/nautilus/key_access.log | grep "FAILED"
```

---

## 访问控制

### 1. 用户认证

#### 1.1 密码策略

```bash
# 环境变量配置
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true
```

#### 1.2 多因素认证（MFA）

```python
# 启用TOTP（基于时间的一次性密码）
# 使用Google Authenticator或类似应用

# 安装依赖
pip install pyotp qrcode

# 生成MFA密钥
import pyotp
secret = pyotp.random_base32()
totp = pyotp.TOTP(secret)
print(f"Secret: {secret}")
print(f"Current OTP: {totp.now()}")
```

#### 1.3 防暴力破解

```bash
# 环境变量配置
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_DURATION=900  # 15分钟

# 速率限制
RATE_LIMIT_LOGIN=5/minute
```

### 2. API访问控制

#### 2.1 API密钥管理

```bash
# 生成API密钥
python3 -c "import secrets; print('nau_' + secrets.token_urlsafe(32))"

# 配置API密钥前缀
API_KEY_PREFIX=nau_
```

#### 2.2 JWT令牌配置

```bash
# JWT配置
JWT_SECRET_KEY=your_strong_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
JWT_REFRESH_EXPIRATION_DAYS=7
```

#### 2.3 IP白名单

```bash
# 配置IP白名单（可选）
IP_WHITELIST=192.168.1.0/24,10.0.0.0/8

# Nginx配置
location /api/admin {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    proxy_pass http://localhost:8000;
}
```

### 3. 数据库访问控制

#### 3.1 数据库用户权限

```sql
-- 创建只读用户
CREATE USER nautilus_readonly WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE nautilus_production TO nautilus_readonly;
GRANT USAGE ON SCHEMA public TO nautilus_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nautilus_readonly;

-- 创建应用用户（限制权限）
CREATE USER nautilus_app WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE nautilus_production TO nautilus_app;
GRANT USAGE ON SCHEMA public TO nautilus_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nautilus_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nautilus_app;
```

#### 3.2 数据库连接加密

```bash
# PostgreSQL SSL配置
# 编辑 postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'

# 连接字符串
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

---

## 安全加固

### 1. 操作系统加固

#### 1.1 系统更新

```bash
# 自动安全更新
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# 手动更新
sudo apt update && sudo apt upgrade -y
```

#### 1.2 禁用不必要的服务

```bash
# 查看运行的服务
systemctl list-units --type=service --state=running

# 禁用不需要的服务
sudo systemctl disable bluetooth
sudo systemctl disable cups
```

#### 1.3 SSH加固

```bash
# 编辑SSH配置
sudo nano /etc/ssh/sshd_config

# 推荐配置
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# 重启SSH
sudo systemctl restart sshd
```

### 2. 应用安全加固

#### 2.1 安全头部

```python
# 已在main.py中配置
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
# Permissions-Policy: geolocation=(), microphone=(), camera=()
```

#### 2.2 CSRF保护

```bash
# 环境变量配置
CSRF_SECRET_KEY=your_csrf_secret_key

# 前端需要获取CSRF token
curl https://yourdomain.com/csrf-token
```

#### 2.3 输入验证

```python
# 所有用户输入都经过验证
# 使用Pydantic模型进行数据验证
# 防止SQL注入、XSS等攻击
```

### 3. 依赖安全

#### 3.1 依赖扫描

```bash
# 安装safety
pip install safety

# 扫描依赖漏洞
safety check

# 更新有漏洞的依赖
pip install --upgrade package_name
```

#### 3.2 定期更新

```bash
# 查看过期依赖
pip list --outdated

# 更新所有依赖（谨慎操作）
pip install --upgrade -r requirements.txt
```

---

## 安全监控

### 1. 日志监控

#### 1.1 安全日志配置

```bash
# 创建安全日志目录
sudo mkdir -p /var/log/nautilus/security
sudo chown nautilus:nautilus /var/log/nautilus/security

# 配置日志级别
LOG_LEVEL=info
AUDIT_LOG_ENABLED=true
AUDIT_LOG_PATH=/var/log/nautilus/security/audit.log
```

#### 1.2 日志分析

```bash
# 分析失败的登录尝试
grep "login failed" /var/log/nautilus/security/audit.log

# 分析异常访问
grep "403\|401" /var/log/nginx/nautilus_access.log

# 分析速率限制触发
grep "rate limit" /var/log/nautilus/app.log
```

### 2. 入侵检测

#### 2.1 安装Fail2ban

```bash
# 安装Fail2ban
sudo apt install fail2ban

# 配置Fail2ban
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/nautilus_error.log
```

#### 2.2 启动Fail2ban

```bash
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# 查看状态
sudo fail2ban-client status
```

### 3. 安全告警

#### 3.1 配置告警规则

```bash
# 监控脚本
cat > /usr/local/bin/security_monitor.sh <<'EOF'
#!/bin/bash

# 检查失败登录次数
FAILED_LOGINS=$(grep "login failed" /var/log/nautilus/security/audit.log | wc -l)
if [ $FAILED_LOGINS -gt 10 ]; then
    echo "WARNING: $FAILED_LOGINS failed login attempts detected" | \
      mail -s "Security Alert" admin@yourdomain.com
fi

# 检查异常访问
FORBIDDEN=$(grep "403" /var/log/nginx/nautilus_access.log | wc -l)
if [ $FORBIDDEN -gt 100 ]; then
    echo "WARNING: $FORBIDDEN forbidden access attempts detected" | \
      mail -s "Security Alert" admin@yourdomain.com
fi
EOF

chmod +x /usr/local/bin/security_monitor.sh

# 添加到cron（每小时执行）
echo "0 * * * * /usr/local/bin/security_monitor.sh" | crontab -
```

---

## 应急响应

### 1. 安全事件响应流程

#### 1.1 发现阶段

```bash
# 检查异常进程
ps aux | grep -v grep | grep suspicious

# 检查网络连接
netstat -tulpn | grep ESTABLISHED

# 检查最近登录
last -n 20
```

#### 1.2 隔离阶段

```bash
# 立即断开网络（紧急情况）
sudo ifconfig eth0 down

# 或阻止特定IP
sudo ufw deny from <suspicious_ip>

# 停止受影响的服务
sudo systemctl stop nautilus-backend
```

#### 1.3 分析阶段

```bash
# 收集日志
tar -czf incident_logs_$(date +%Y%m%d).tar.gz /var/log/nautilus/

# 分析访问日志
grep <suspicious_ip> /var/log/nginx/nautilus_access.log

# 检查文件完整性
find /home/nautilus -type f -mtime -1
```

#### 1.4 恢复阶段

```bash
# 从备份恢复
./rollback.sh

# 更新密钥
python3 setup_key_management.py --rotate

# 重启服务
sudo systemctl start nautilus-backend
```

### 2. 数据泄露响应

```bash
# 1. 立即更改所有密钥和密码
# 2. 通知受影响用户
# 3. 审查访问日志
# 4. 加强安全措施
# 5. 向监管机构报告（如需要）
```

### 3. 联系方式

**安全团队**: security@nautilus.com
**紧急热线**: +1-xxx-xxx-xxxx
**事件报告**: https://security.nautilus.com/report

---

**文档版本**: 1.0
**最后更新**: 2026-02-26
