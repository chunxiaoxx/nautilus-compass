# 🚀 生产环境部署快速参考

**Nautilus Phase 3 Backend - 生产部署速查表**

---

## 📋 部署前快速检查（5分钟）

```bash
# 1. 检查文件是否存在
ls -l .env.production.example
ls -l PRODUCTION_DEPLOYMENT_CHECKLIST.md
ls -l PRODUCTION_DEPLOYMENT_GUIDE.md
ls -l PRODUCTION_SECURITY_GUIDE.md

# 2. 复制配置文件
cp .env.production.example .env.production

# 3. 生成密钥
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('CSRF_SECRET_KEY=' + secrets.token_urlsafe(32))"

# 4. 编辑配置（修改所有 [必须修改] 的项）
nano .env.production

# 5. 设置权限
chmod 600 .env.production
```

---

## 🔑 必须修改的配置项（15项）

```bash
# 环境标识
ENVIRONMENT=production
DEBUG=false
FORCE_HTTPS=true

# 密钥（使用上面生成的）
JWT_SECRET_KEY=<生成的强随机密钥>
CSRF_SECRET_KEY=<生成的强随机密钥>

# 数据库
DATABASE_URL=postgresql://user:STRONG_PASSWORD@host:5432/nautilus_production

# Redis
REDIS_URL=redis://:STRONG_PASSWORD@localhost:6379/0

# CORS（替换为实际域名）
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 区块链
INFURA_PROJECT_ID=YOUR_INFURA_PROJECT_ID
BLOCKCHAIN_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
BLOCKCHAIN_ACCOUNT_ADDRESS=0xYOUR_ADDRESS

# 智能合约地址（部署后填入）
IDENTITY_CONTRACT_ADDRESS=0x...
TASK_CONTRACT_ADDRESS=0x...
REWARD_CONTRACT_ADDRESS=0x...

# 密钥管理（选择一种方式）
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=/secure/path/to/encrypted_key.json
KEY_ENCRYPTION_PASSWORD=STRONG_ENCRYPTION_PASSWORD
```

---

## 🛠️ 快速部署命令（30分钟）

```bash
# 1. 安装系统依赖
sudo apt update
sudo apt install -y python3 python3-pip postgresql redis nginx certbot

# 2. 配置数据库
sudo -u postgres psql <<EOF
CREATE DATABASE nautilus_production;
CREATE USER nautilus_user WITH ENCRYPTED PASSWORD 'STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE nautilus_production TO nautilus_user;
EOF

# 3. 配置Redis
sudo nano /etc/redis/redis.conf
# 设置: requirepass STRONG_PASSWORD
sudo systemctl restart redis

# 4. 获取SSL证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 5. 安装Python依赖
pip3 install -r requirements.txt

# 6. 设置密钥管理
python3 setup_key_management.py

# 7. 执行部署
ENVIRONMENT=production ./deploy_blockchain.sh

# 8. 验证部署
curl https://yourdomain.com/health
```

---

## ✅ 部署后验证（10分钟）

```bash
# 1. 检查服务状态
systemctl status nautilus-backend

# 2. 检查健康状态
curl https://yourdomain.com/health

# 3. 检查日志
tail -f /var/log/nautilus/app.log

# 4. 测试API
curl https://yourdomain.com/

# 5. 测试认证
curl -X POST https://yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# 6. 检查SSL评级
# 访问: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com

# 7. 测试速率限制
for i in {1..10}; do curl -X POST https://yourdomain.com/api/auth/login; done

# 8. 检查数据库连接
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM agents;"

# 9. 检查Redis连接
redis-cli -u "$REDIS_URL" ping

# 10. 检查区块链连接
curl https://yourdomain.com/api/blockchain/status
```

---

## 🔥 常见问题快速修复

### 问题1: 服务无法启动
```bash
# 查看日志
sudo journalctl -u nautilus-backend -n 50

# 检查配置
python3 -c "from main import app; print('OK')"

# 检查端口
netstat -tlnp | grep 8000
```

### 问题2: 数据库连接失败
```bash
# 测试连接
psql "$DATABASE_URL" -c "SELECT 1;"

# 检查PostgreSQL
sudo systemctl status postgresql

# 检查配置
grep DATABASE_URL .env.production
```

### 问题3: SSL证书问题
```bash
# 检查证书
sudo certbot certificates

# 续期证书
sudo certbot renew

# 测试SSL
openssl s_client -connect yourdomain.com:443
```

### 问题4: 性能问题
```bash
# 检查资源
top
free -h
df -h

# 增加Worker数量
# 编辑 .env.production: WORKERS=8

# 重启服务
sudo systemctl restart nautilus-backend
```

---

## 🔄 快速回滚

```bash
# 1. 停止服务
sudo systemctl stop nautilus-backend

# 2. 恢复代码
git checkout <previous-commit>

# 3. 恢复数据库
psql "$DATABASE_URL" < backups/nautilus_backup_YYYYMMDD_HHMMSS.sql

# 4. 重启服务
sudo systemctl start nautilus-backend

# 5. 验证
curl https://yourdomain.com/health
```

---

## 📞 紧急联系

- **技术支持**: support@nautilus.com
- **安全团队**: security@nautilus.com
- **紧急热线**: +1-xxx-xxx-xxxx

---

## 📚 详细文档

| 文档 | 用途 |
|------|------|
| `PRODUCTION_DEPLOYMENT_CHECKLIST.md` | 完整检查清单 |
| `PRODUCTION_DEPLOYMENT_GUIDE.md` | 详细部署指南 |
| `PRODUCTION_SECURITY_GUIDE.md` | 安全配置指南 |
| `DEPLOYMENT_PREPARATION_REPORT.md` | 准备工作报告 |

---

## ⏱️ 时间估算

| 阶段 | 时间 |
|------|------|
| 配置准备 | 1-2小时 |
| 服务器准备 | 2-3小时 |
| 部署执行 | 30分钟 |
| 部署验证 | 1小时 |
| **总计** | **4-6小时** |

---

**版本**: 1.0
**更新**: 2026-02-26
