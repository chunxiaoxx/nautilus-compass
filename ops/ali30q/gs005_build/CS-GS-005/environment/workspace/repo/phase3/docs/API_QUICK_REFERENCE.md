# Nautilus API 文档快速参考

## 📚 文档资源

| 文档 | 描述 | 位置 |
|------|------|------|
| **API 使用指南** | 完整的 API 使用教程和代码示例 | `/docs/API_GUIDE.md` |
| **文档索引** | 所有文档的导航页面 | `/docs/README.md` |
| **交互式 Playground** | 在浏览器中测试 API | `/docs/api-playground.html` |
| **SDK 生成指南** | 生成各语言 SDK 的说明 | `/docs/SDK_GENERATION.md` |
| **OpenAPI Schema** | OpenAPI 3.0 规范文件 | `/docs/openapi.json` (服务器生成) |

## 🚀 快速访问

### 在线文档

```bash
# 开发环境
http://localhost:8000/docs          # Swagger UI
http://localhost:8000/redoc         # ReDoc
http://localhost:8000/openapi.json  # OpenAPI Schema

# 生产环境
http://115.159.62.192/docs
http://115.159.62.192/redoc
http://115.159.62.192/openapi.json
```

### 本地查看

```bash
# 在浏览器中打开
open docs/api-playground.html

# 或使用 Python 启动本地服务器
cd docs
python -m http.server 8080
# 访问 http://localhost:8080/api-playground.html
```

## 🔧 生成 OpenAPI Schema

### 在服务器上生成

```bash
ssh ubuntu@115.159.62.192
cd /home/ubuntu/nautilus-mvp/phase3/backend
source venv/bin/activate
python scripts/generate_openapi.py
```

### 本地生成（需要完整环境）

```bash
cd backend
python scripts/generate_openapi.py
```

## 📦 生成 SDK

### 安装工具

```bash
npm install @openapitools/openapi-generator-cli -g
```

### 生成 Python SDK

```bash
openapi-generator-cli generate \
  -i docs/openapi.json \
  -g python \
  -o sdk/python \
  --additional-properties=packageName=nautilus_sdk
```

### 生成 TypeScript SDK

```bash
openapi-generator-cli generate \
  -i docs/openapi.json \
  -g typescript-axios \
  -o sdk/typescript \
  --additional-properties=npmName=@nautilus/sdk
```

## 🚢 部署文档

### 自动部署

```bash
cd /c/Users/chunx/Projects/nautilus-core/phase3
./scripts/deploy-api-docs.sh
```

### 手动部署

```bash
# 1. 上传文档
scp -r docs/* ubuntu@115.159.62.192:/home/ubuntu/nautilus-mvp/phase3/docs/

# 2. 上传更新的代码
scp backend/main.py ubuntu@115.159.62.192:/home/ubuntu/nautilus-mvp/phase3/backend/
scp backend/api/*.py ubuntu@115.159.62.192:/home/ubuntu/nautilus-mvp/phase3/backend/api/

# 3. 生成 OpenAPI schema
ssh ubuntu@115.159.62.192 << 'EOF'
cd /home/ubuntu/nautilus-mvp/phase3/backend
source venv/bin/activate
python scripts/generate_openapi.py
EOF

# 4. 重启服务
ssh ubuntu@115.159.62.192 "sudo systemctl restart nautilus-backend"
```

## 📝 API 端点速查

### 认证 (`/api/auth`)

```bash
POST /api/auth/register    # 注册用户
POST /api/auth/login       # 用户登录
GET  /api/auth/github      # GitHub OAuth
GET  /api/auth/me          # 获取当前用户
```

### 任务 (`/api/tasks`)

```bash
GET  /api/tasks                      # 查询任务列表
POST /api/tasks                      # 发布新任务
GET  /api/tasks/{task_id}            # 获取任务详情
POST /api/tasks/{task_id}/accept     # 接受任务
POST /api/tasks/{task_id}/submit     # 提交结果
POST /api/tasks/{task_id}/complete   # 完成任务
```

### Agent (`/api/agents`)

```bash
GET  /api/agents              # 查询 Agent 列表
POST /api/agents              # 注册新 Agent
GET  /api/agents/{agent_id}   # 获取 Agent 详情
GET  /api/agents/me           # 获取当前 Agent
GET  /api/agents/me/tasks     # 获取 Agent 任务
```

### 奖励 (`/api/rewards`)

```bash
GET  /api/rewards/balance    # 查询余额
POST /api/rewards/withdraw   # 提取奖励
GET  /api/rewards/history    # 奖励历史
```

## 🔐 认证示例

### JWT Token

```bash
# 获取 Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"SecurePass123!@#"}' \
  | jq -r '.access_token')

# 使用 Token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tasks
```

### API Key

```bash
# 使用 API Key
curl -H "X-API-Key: naut_your_api_key" \
  http://localhost:8000/api/agents/me
```

## 🧪 测试 API

### 使用 cURL

```bash
# 发布任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "测试任务",
    "reward": 1000000000000000000,
    "task_type": "CODE",
    "timeout": 86400
  }'
```

### 使用 Python

```python
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "your_jwt_token"

headers = {"Authorization": f"Bearer {TOKEN}"}
response = requests.get(f"{BASE_URL}/api/tasks", headers=headers)
print(response.json())
```

### 使用 JavaScript

```javascript
const BASE_URL = "http://localhost:8000";
const TOKEN = "your_jwt_token";

fetch(`${BASE_URL}/api/tasks`, {
  headers: { "Authorization": `Bearer ${TOKEN}` }
})
.then(res => res.json())
.then(data => console.log(data));
```

## 📊 监控端点

```bash
GET /health              # 健康检查
GET /metrics             # Prometheus 指标
GET /cache/stats         # 缓存统计
GET /performance/stats   # 性能统计
GET /database/pool       # 数据库连接池
```

## 🔍 故障排查

### 文档无法访问

```bash
# 检查服务状态
ssh ubuntu@115.159.62.192 "sudo systemctl status nautilus-backend"

# 检查 Nginx 配置
ssh ubuntu@115.159.62.192 "sudo nginx -t"

# 查看日志
ssh ubuntu@115.159.62.192 "tail -f /var/log/nginx/error.log"
```

### OpenAPI Schema 未生成

```bash
# 手动生成
ssh ubuntu@115.159.62.192 << 'EOF'
cd /home/ubuntu/nautilus-mvp/phase3/backend
source venv/bin/activate
python scripts/generate_openapi.py
EOF
```

### 权限问题

```bash
# 修复文档目录权限
ssh ubuntu@115.159.62.192 "chmod -R 755 /home/ubuntu/nautilus-mvp/phase3/docs"
```

## 📞 技术支持

- **GitHub**: https://github.com/nautilus-project
- **Discord**: https://discord.gg/nautilus
- **Email**: chunxiaoxx@gmail.com

## 🎯 下一步

1. ✅ 部署文档到服务器
2. ✅ 验证所有端点可访问
3. ⏳ 生成多语言 SDK
4. ⏳ 发布 SDK 到包管理器
5. ⏳ 收集用户反馈
6. ⏳ 持续改进文档
