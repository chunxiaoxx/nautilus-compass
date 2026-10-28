# 在服务器控制台执行的命令

## 第1步：修复API密钥生成（datetime导入）

```bash
sed -i '1i from datetime import datetime' ~/nautilus-mvp/phase3/backend/api/auth.py
```

## 第2步：验证修复

```bash
head -5 ~/nautilus-mvp/phase3/backend/api/auth.py
```

应该看到第一行是：`from datetime import datetime`

## 第3步：等待后端重新加载并检查日志

```bash
sleep 3
tail -20 ~/backend.log
```

确认没有错误信息。

## 第4步：测试API密钥生成

```bash
TOKEN=$(curl -s -X POST https://api.nautilus.social/api/auth/login -H 'Content-Type: application/json' -d '{"username":"testuser999","password":"Test@123456789"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: $TOKEN"

curl -X POST https://api.nautilus.social/api/auth/api-keys/generate -H "Authorization: Bearer $TOKEN"
```

应该返回类似：`{"api_key":"naut_xxxxx","created_at":"2026-02-23T...","user_id":1}`

---

**执行完这4步后，API密钥生成功能就修复了！**
