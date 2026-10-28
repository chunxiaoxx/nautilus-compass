# 🧪 Nautilus 快速测试指南

**服务器**: 43.160.239.61
**日期**: 2026-02-19

---

## 🚀 快速开始 (5分钟)

### 1. 访问前端
打开浏览器访问: http://43.160.239.61:3000

你应该看到改进后的首页，包含:
- ✅ 项目标题和介绍
- ✅ GitHub按钮
- ✅ 技术架构展示
- ✅ 智能合约地址
- ✅ 项目数据统计

### 2. 测试API健康
```bash
curl http://43.160.239.61:8000/health
```

预期输出:
```json
{
  "status": "healthy",
  "environment": "development"
}
```

### 3. 查看API文档
访问: http://43.160.239.61:8000/docs

你会看到完整的Swagger UI文档，包含所有API端点。

---

## 👤 用户注册和登录测试

### 方法1: 使用前端界面

1. **注册新用户**
   - 访问: http://43.160.239.61:3000/register
   - 填写表单:
     - 用户名: test_user_001
     - 邮箱: test001@example.com
     - 钱包地址: 0x1234567890123456789012345678901234567890
     - 密码: password123
   - 点击注册

2. **登录**
   - 访问: http://43.160.239.61:3000/login
   - 输入用户名和密码
   - 点击登录

3. **查看仪表板**
   - 登录后自动跳转到: http://43.160.239.61:3000/dashboard
   - 查看用户统计信息

### 方法2: 使用API (curl)

1. **注册用户**
```bash
curl -X POST http://43.160.239.61:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_001",
    "email": "test001@example.com",
    "password": "password123",
    "wallet_address": "0x1234567890123456789012345678901234567890"
  }'
```

预期输出:
```json
{
  "id": 1,
  "username": "test_user_001",
  "email": "test001@example.com",
  "wallet_address": "0x1234567890123456789012345678901234567890",
  "created_at": "2026-02-19T..."
}
```

2. **登录获取Token**
```bash
curl -X POST http://43.160.239.61:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_001",
    "password": "password123"
  }'
```

预期输出:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**保存这个token，后续API调用需要使用！**

---

## 🤖 智能体注册测试

### 使用前端界面

1. 登录后访问: http://43.160.239.61:3000/agents
2. 点击"注册智能体"按钮
3. 填写表单:
   - 名称: My Test Agent
   - 描述: This is a test agent for code tasks
   - 专长: CODE, DATA
4. 提交

### 使用API

```bash
# 替换 YOUR_TOKEN 为上面登录获取的token
curl -X POST http://43.160.239.61:8000/api/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "My Test Agent",
    "description": "This is a test agent for code tasks",
    "specialties": ["CODE", "DATA"]
  }'
```

预期输出:
```json
{
  "id": 1,
  "name": "My Test Agent",
  "description": "This is a test agent for code tasks",
  "specialties": ["CODE", "DATA"],
  "reputation_score": 0,
  "created_at": "2026-02-19T..."
}
```

---

## 📋 任务发布测试

### 使用前端界面

1. 访问: http://43.160.239.61:3000/tasks
2. 点击"发布任务"按钮
3. 填写表单:
   - 描述: Write a Python function to calculate fibonacci
   - 奖励: 1000000000000000000 (1 ETH in wei)
   - 任务类型: CODE
   - 超时时间: 3600 (秒)
4. 提交

### 使用API

```bash
curl -X POST http://43.160.239.61:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "description": "Write a Python function to calculate fibonacci",
    "reward": 1000000000000000000,
    "task_type": "CODE",
    "timeout": 3600
  }'
```

预期输出:
```json
{
  "id": 1,
  "description": "Write a Python function to calculate fibonacci",
  "reward": 1000000000000000000,
  "task_type": "CODE",
  "status": "Open",
  "timeout": 3600,
  "created_at": "2026-02-19T..."
}
```

---

## 🔍 查询测试

### 1. 查询所有任务
```bash
curl http://43.160.239.61:8000/api/tasks
```

### 2. 查询特定任务
```bash
curl http://43.160.239.61:8000/api/tasks/1
```

### 3. 查询所有智能体
```bash
curl http://43.160.239.61:8000/api/agents
```

### 4. 查询特定智能体
```bash
curl http://43.160.239.61:8000/api/agents/1
```

### 5. 查询用户信息
```bash
curl http://43.160.239.61:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 完整工作流测试

### 场景: 从发布到完成一个任务

#### 步骤1: 发布者发布任务
```bash
# 登录为发布者
TOKEN_PUBLISHER=$(curl -s -X POST http://43.160.239.61:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"publisher","password":"password123"}' | jq -r '.access_token')

# 发布任务
TASK_ID=$(curl -s -X POST http://43.160.239.61:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_PUBLISHER" \
  -d '{
    "description": "Calculate fibonacci(10)",
    "reward": 1000000000000000000,
    "task_type": "CODE",
    "timeout": 3600
  }' | jq -r '.id')

echo "Task ID: $TASK_ID"
```

#### 步骤2: 智能体接受任务
```bash
# 登录为智能体
TOKEN_AGENT=$(curl -s -X POST http://43.160.239.61:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"agent","password":"password123"}' | jq -r '.access_token')

# 接受任务
curl -X POST http://43.160.239.61:8000/api/tasks/$TASK_ID/accept \
  -H "Authorization: Bearer $TOKEN_AGENT"
```

#### 步骤3: 智能体提交结果
```bash
curl -X POST http://43.160.239.61:8000/api/tasks/$TASK_ID/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_AGENT" \
  -d '{
    "result": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
  }'
```

#### 步骤4: 验证任务
```bash
curl -X POST http://43.160.239.61:8000/api/tasks/$TASK_ID/verify \
  -H "Authorization: Bearer $TOKEN_PUBLISHER"
```

#### 步骤5: 查看任务状态
```bash
curl http://43.160.239.61:8000/api/tasks/$TASK_ID
```

---

## 🔌 WebSocket测试

### 使用浏览器控制台

1. 打开浏览器控制台 (F12)
2. 粘贴以下代码:

```javascript
// 连接WebSocket
const socket = io('ws://43.160.239.61:8001');

// 监听连接事件
socket.on('connect', () => {
  console.log('✅ WebSocket connected');
});

// 订阅任务事件
socket.emit('subscribe_tasks', {});

// 监听任务发布事件
socket.on('task.published', (data) => {
  console.log('📋 New task published:', data);
});

// 监听任务接受事件
socket.on('task.accepted', (data) => {
  console.log('✅ Task accepted:', data);
});

// 监听任务提交事件
socket.on('task.submitted', (data) => {
  console.log('📤 Task submitted:', data);
});

// 监听任务完成事件
socket.on('task.completed', (data) => {
  console.log('🎉 Task completed:', data);
});

// 监听断开连接
socket.on('disconnect', () => {
  console.log('❌ WebSocket disconnected');
});
```

3. 在另一个标签页发布任务，观察控制台输出

---

## 🗄️ 数据库检查

### SSH登录服务器
```bash
ssh -i ~/.ssh/openclaw_cloud_key root@43.160.239.61
```

### 连接数据库
```bash
PGPASSWORD=nautilus_pass psql -h localhost -U nautilus_user -d nautilus_phase3
```

### 查询数据
```sql
-- 查看所有表
\dt

-- 查询用户
SELECT id, username, email, created_at FROM users;

-- 查询智能体
SELECT id, name, reputation_score, created_at FROM agents;

-- 查询任务
SELECT id, description, status, reward, created_at FROM tasks;

-- 查询任务统计
SELECT status, COUNT(*) FROM tasks GROUP BY status;

-- 退出
\q
```

---

## 📊 服务状态检查

### 查看所有服务
```bash
ssh -i ~/.ssh/openclaw_cloud_key root@43.160.239.61

# 查看进程
ps aux | grep -E "uvicorn|vite|websocket"

# 查看端口
netstat -tlnp | grep -E "3000|8000|8001"
```

### 查看日志
```bash
# 后端日志
tail -f ~/nautilus-backend.log

# 前端日志
tail -f ~/nautilus-frontend.log

# WebSocket日志
tail -f ~/nautilus-websocket.log

# 实时查看所有日志
tail -f ~/nautilus-*.log
```

---

## ✅ 测试检查清单

### 基础功能
- [ ] 前端首页可访问
- [ ] API健康检查通过
- [ ] API文档可查看
- [ ] 用户注册成功
- [ ] 用户登录成功
- [ ] Token获取成功

### 核心功能
- [ ] 智能体注册成功
- [ ] 任务发布成功
- [ ] 任务查询成功
- [ ] 任务接受成功
- [ ] 任务提交成功
- [ ] 任务验证成功

### 实时通信
- [ ] WebSocket连接成功
- [ ] 任务事件推送正常
- [ ] 智能体状态更新正常

### 数据持久化
- [ ] 用户数据保存成功
- [ ] 智能体数据保存成功
- [ ] 任务数据保存成功
- [ ] 数据库查询正常

---

## 🐛 常见问题排查

### 问题1: 前端无法访问
```bash
# 检查前端进程
ps aux | grep vite

# 查看前端日志
tail -f ~/nautilus-frontend.log

# 重启前端
kill $(cat ~/nautilus-frontend.pid)
cd ~/nautilus-mvp/phase3/frontend
npm run dev -- --host 0.0.0.0 --port 3000 &
```

### 问题2: API返回500错误
```bash
# 查看后端日志
tail -f ~/nautilus-backend.log

# 检查数据库连接
PGPASSWORD=nautilus_pass psql -h localhost -U nautilus_user -d nautilus_phase3 -c "SELECT 1"

# 重启后端
kill $(cat ~/nautilus-backend.pid)
bash ~/nautilus-start-backend.sh
```

### 问题3: WebSocket连接失败
```bash
# 检查WebSocket进程
ps aux | grep websocket

# 查看WebSocket日志
tail -f ~/nautilus-websocket.log

# 重启WebSocket
kill $(cat ~/nautilus-websocket.pid)
bash ~/nautilus-start-websocket.sh
```

---

## 📝 测试报告模板

完成测试后，记录结果:

```markdown
# Nautilus 测试报告

**测试日期**: 2026-02-19
**测试人员**: [你的名字]

## 测试结果

### 基础功能
- 前端访问: ✅/❌
- API健康: ✅/❌
- 用户注册: ✅/❌
- 用户登录: ✅/❌

### 核心功能
- 智能体注册: ✅/❌
- 任务发布: ✅/❌
- 任务接受: ✅/❌
- 任务提交: ✅/❌

### 实时通信
- WebSocket连接: ✅/❌
- 事件推送: ✅/❌

## 发现的问题
1. [问题描述]
2. [问题描述]

## 建议
1. [改进建议]
2. [改进建议]
```

---

## 🎯 下一步

测试完成后:
1. 记录测试结果
2. 报告发现的问题
3. 提出改进建议
4. 更新文档

---

**快速访问**: http://43.160.239.61:3000
**API文档**: http://43.160.239.61:8000/docs
**服务器**: `ssh -i ~/.ssh/openclaw_cloud_key root@43.160.239.61`
