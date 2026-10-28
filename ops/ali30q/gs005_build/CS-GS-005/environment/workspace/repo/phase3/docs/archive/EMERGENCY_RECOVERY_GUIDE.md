# 🚨 服务器紧急恢复指南

**执行环境**: 腾讯云 VNC 控制台
**执行时间**: 2026-03-02

---

## 🔧 Step 1: 修复防火墙配置 (5 分钟)

### 1.1 检查当前状态
```bash
sudo ufw status verbose
```

### 1.2 重置并重新配置防火墙
```bash
# 重置防火墙（如果配置错误）
sudo ufw --force reset

# 设置默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 添加必要的端口规则
sudo ufw allow 24860/tcp  # SSH (自定义端口) ⚠️ 最重要
sudo ufw allow 22/tcp     # SSH (标准端口，备用)
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS

# 启用防火墙
sudo ufw enable

# 验证配置
sudo ufw status numbered
```

**预期输出**:
```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 24860/tcp                  ALLOW IN    Anywhere
[ 2] 22/tcp                     ALLOW IN    Anywhere
[ 3] 80/tcp                     ALLOW IN    Anywhere
[ 4] 443/tcp                    ALLOW IN    Anywhere
```

---

## 🔧 Step 2: 修复数据库配置 (5 分钟)

### 2.1 备份当前文件
```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend
cp utils/database.py utils/database.py.backup.$(date +%Y%m%d_%H%M%S)
```

### 2.2 修改 database.py
```bash
# 在文件顶部添加 load_dotenv()
sudo nano utils/database.py
```

**在第 4 行后添加**:
```python
from dotenv import load_dotenv

# Load environment variables BEFORE any configuration
load_dotenv()
```

**或者使用 sed 自动添加**:
```bash
sudo sed -i '4a\\nfrom dotenv import load_dotenv\n\n# Load environment variables BEFORE any configuration\nload_dotenv()' utils/database.py
```

### 2.3 验证修改
```bash
head -20 utils/database.py
```

---

## 🔧 Step 3: 重启服务 (2 分钟)

### 3.1 停止当前服务
```bash
pkill -f uvicorn
```

### 3.2 启动服务
```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/nautilus-api.log 2>&1 &
```

### 3.3 检查服务状态
```bash
# 等待 10 秒
sleep 10

# 检查进程
ps aux | grep uvicorn | grep -v grep

# 检查日志
tail -50 /tmp/nautilus-api.log
```

---

## 🔧 Step 4: 验证修复 (5 分钟)

### 4.1 测试 SSH 连接
```bash
# 从本地测试
ssh cloud "echo 'SSH OK'"
```

### 4.2 测试前端
```bash
curl -I https://nautilus.social
# 预期: HTTP/1.1 200 OK
```

### 4.3 测试 API
```bash
curl -s https://api.nautilus.social/health | python3 -m json.tool
```

**预期输出**:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "3.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "connected": true
    },
    "blockchain": {
      "status": "healthy",
      "connected": true
    },
    "redis": {
      "status": "healthy",
      "connected": true
    }
  }
}
```

---

## 🔧 Step 5: 部署 OAuth 修复 (可选，20 分钟)

### 5.1 上传修复文件
```bash
# 从本地上传
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
scp api/auth_google.py cloud:/home/ubuntu/nautilus-mvp/phase3/backend/api/
scp migrations/add_google_oauth.sql cloud:/home/ubuntu/nautilus-mvp/phase3/backend/migrations/
scp deploy_oauth_onestep.sh cloud:/home/ubuntu/nautilus-mvp/phase3/backend/
```

### 5.2 执行部署
```bash
ssh cloud "cd /home/ubuntu/nautilus-mvp/phase3/backend && chmod +x deploy_oauth_onestep.sh && ./deploy_oauth_onestep.sh"
```

---

## 📋 检查清单

### 防火墙
- [ ] UFW 状态为 active
- [ ] SSH 端口 24860 已允许
- [ ] HTTP/HTTPS 端口已允许
- [ ] 可以从外部 SSH 连接

### 数据库
- [ ] database.py 已添加 load_dotenv()
- [ ] 服务使用 PostgreSQL 而非 SQLite
- [ ] 健康检查显示数据库 connected

### 服务
- [ ] 后端 API 运行正常
- [ ] 前端可以访问
- [ ] 健康检查返回 healthy

### OAuth (可选)
- [ ] Google OAuth 代码已部署
- [ ] 数据库迁移已执行
- [ ] OAuth 端点可访问

---

## 🚨 故障排查

### 如果 SSH 仍然无法连接
```bash
# 检查防火墙状态
sudo ufw status verbose

# 检查 SSH 服务
sudo systemctl status ssh

# 检查端口监听
sudo netstat -tlnp | grep 24860
```

### 如果服务无法启动
```bash
# 检查错误日志
tail -100 /tmp/nautilus-api.log

# 检查 Python 环境
python3 --version
which python3

# 检查依赖
pip3 list | grep fastapi
```

### 如果数据库连接失败
```bash
# 检查 PostgreSQL
sudo docker ps | grep postgres

# 检查环境变量
cat .env | grep DATABASE_URL

# 测试数据库连接
python3 -c "from utils.database import engine; print(engine.url)"
```

---

## 📞 紧急联系

如果遇到无法解决的问题：
1. 保持 VNC 控制台连接
2. 截图错误信息
3. 记录执行的命令
4. 寻求技术支持

---

**执行顺序**: Step 1 → Step 2 → Step 3 → Step 4 → (可选) Step 5

**预计总时间**: 15-20 分钟

**风险等级**: 低（所有操作都有备份和回滚方案）

---

*Emergency Recovery Guide - 2026-03-02*
