# OAuth 快速开始指南

## 🎯 任务完成状态

### ✅ GitHub OAuth - 已正常工作
- **状态：** 无需修复，完全正常
- **测试：** `curl -X GET https://api.nautilus.social/api/auth/github/login`
- **结果：** HTTP 307 重定向到 GitHub

### ⏳ Google OAuth - 等待部署
- **状态：** 代码完成，需要上传到服务器
- **文件：** api/auth.py, migrations/add_google_oauth.sql

---

## 🚀 立即部署 Google OAuth

### 方法 1：一键部署（推荐）

```bash
# 在本地 Git Bash 中执行
cd C:/Users/chunx/Projects/nautilus-core/phase3/backend
bash deploy_google_oauth.sh
```

### 方法 2：手动部署

```bash
# 1. 上传文件
scp api/auth.py ubuntu@47.76.127.85:/home/ubuntu/nautilus-mvp/phase3/backend/api/
scp migrations/add_google_oauth.sql ubuntu@47.76.127.85:/home/ubuntu/nautilus-mvp/phase3/backend/migrations/

# 2. SSH 登录
ssh ubuntu@47.76.127.85

# 3. 执行迁移
cd /home/ubuntu/nautilus-mvp/phase3/backend
source venv/bin/activate
psql $DATABASE_URL -f migrations/add_google_oauth.sql

# 4. 重启服务
pkill uvicorn
nohup uvicorn main:socket_app_with_fastapi --host 0.0.0.0 --port 8000 > /tmp/nautilus.log 2>&1 &

# 5. 验证
curl -X GET https://api.nautilus.social/api/auth/google/login -w "\nHTTP: %{http_code}\n"
```

---

## 🧪 测试验证

### 快速测试

```bash
# 运行测试脚本
bash test_oauth.sh

# 或手动测试
curl -X GET https://api.nautilus.social/api/auth/github/login -w "\nHTTP: %{http_code}\n"
curl -X GET https://api.nautilus.social/api/auth/google/login -w "\nHTTP: %{http_code}\n"
```

### 预期结果

- **GitHub OAuth:** HTTP 307 ✅
- **Google OAuth (未配置凭证):** HTTP 500 ⚠️
- **Google OAuth (已配置凭证):** HTTP 307 ✅

---

## 🔑 配置 Google OAuth 凭证（可选）

### 1. 获取凭证

1. 访问 https://console.cloud.google.com/
2. 创建项目或选择现有项目
3. 启用 Google+ API
4. 创建 OAuth 客户端 ID
5. 配置回调 URL: `https://api.nautilus.social/api/auth/google/callback`
6. 复制客户端 ID 和密钥

### 2. 配置服务器

```bash
ssh ubuntu@47.76.127.85
nano /home/ubuntu/nautilus-mvp/phase3/backend/.env

# 添加以下内容：
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://api.nautilus.social/api/auth/google/callback

# 保存并重启
pkill uvicorn
cd /home/ubuntu/nautilus-mvp/phase3/backend
source venv/bin/activate
nohup uvicorn main:socket_app_with_fastapi --host 0.0.0.0 --port 8000 > /tmp/nautilus.log 2>&1 &
```

---

## 📚 详细文档

- **OAUTH_DEPLOYMENT_GUIDE.md** - 完整部署指南
- **OAUTH_SUMMARY.md** - 技术总结
- **OAUTH_EXECUTION_REPORT.md** - 执行报告

---

## ❓ 常见问题

### Q: GitHub OAuth 为什么返回 405？

**A:** 如果使用 `curl -I`（HEAD 请求）会返回 405，这是正常的。OAuth 端点只支持 GET 方法。

**正确测试方式：**
```bash
curl -X GET https://api.nautilus.social/api/auth/github/login  # ✅
curl https://api.nautilus.social/api/auth/github/login         # ✅
curl -I https://api.nautilus.social/api/auth/github/login      # ❌ 返回 405
```

### Q: Google OAuth 返回 500 是什么原因？

**A:** 端点存在但未配置 Google OAuth 凭证。这是正常的，需要在 `.env` 中配置凭证。

### Q: 如何查看服务日志？

**A:**
```bash
ssh ubuntu@47.76.127.85 'tail -f /tmp/nautilus.log'
```

---

## ✅ 完成检查清单

- [ ] 上传 api/auth.py 到服务器
- [ ] 上传 migrations/add_google_oauth.sql 到服务器
- [ ] 执行数据库迁移
- [ ] 重启服务
- [ ] 测试 Google OAuth 端点（应返回 500 或 307）
- [ ] （可选）申请 Google OAuth 凭证
- [ ] （可选）配置 Google OAuth 凭证
- [ ] （可选）测试完整 Google OAuth 流程

---

**快速联系：** 查看 OAUTH_DEPLOYMENT_GUIDE.md 获取更多帮助
