# 🧪 端到端测试指南

## Task #28: 端到端测试完整流程

**目标**: 测试从用户注册到任务完成的完整区块链集成流程

---

## 📋 测试准备

### 1. 环境要求
- ✅ 后端服务运行中
- ✅ 数据库已迁移
- ✅ 区块链配置正确
- ✅ 测试账户有足够ETH

### 2. 工具准备
- curl 或 Postman
- JWT token
- API Key
- Sepolia浏览器

---

## 🚀 完整测试流程

### 步骤1: 用户注册
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "password": "Test123456",
    "wallet_address": "0x7809b48a102755776436aa2948d1e42d2377465d"
  }'
```

**预期响应**:
```json
{
  "id": 1,
  "username": "test_user",
  "email": "test@example.com",
  "wallet_address": "0x7809b48a102755776436aa2948d1e42d2377465d"
}
```

---

### 步骤2: 用户登录
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "Test123456"
  }'
```

**预期响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**保存JWT Token**: `export JWT_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."`

---

### 步骤3: 注册Agent（链上注册）⭐
```bash
curl -X POST http://localhost:8000/api/agents \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "description": "E2E test agent",
    "specialties": ["CODE", "DATA"]
  }'
```

**预期响应**:
```json
{
  "agent": {
    "agent_id": 1,
    "name": "Test Agent",
    "blockchain_registered": true,
    "blockchain_tx_hash": "0xabc123...",
    "blockchain_address": "0x7809b48a102755776436aa2948d1e42d2377465d"
  },
  "api_key": "nau_..."
}
```

**验证点**:
- ✅ blockchain_registered = true
- ✅ blockchain_tx_hash 存在
- ✅ 在Sepolia浏览器查看交易

**保存API Key**: `export API_KEY="nau_..."`

---

### 步骤4: 查询Agent链上状态
```bash
curl -X GET http://localhost:8000/api/agents/1/blockchain-status
```

**预期响应**:
```json
{
  "agent_id": 1,
  "owner": "0x7809b48a102755776436aa2948d1e42d2377465d",
  "database_registered": true,
  "blockchain_registered": true,
  "blockchain_tx_hash": "0xabc123...",
  "on_chain_registered": true,
  "on_chain_data": {
    "name": "Test Agent",
    "owner": "0x7809b48a102755776436aa2948d1e42d2377465d"
  }
}
```

---

### 步骤5: 发布任务（链上发布）⭐
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "E2E test task - blockchain integration",
    "reward": 1000000000000000000,
    "task_type": "CODE",
    "timeout": 3600
  }'
```

**预期响应**:
```json
{
  "id": 1,
  "task_id": "task_1234567890",
  "description": "E2E test task - blockchain integration",
  "reward": 1000000000000000000,
  "status": "Open",
  "blockchain_tx_hash": "0xdef456...",
  "blockchain_status": "published"
}
```

**验证点**:
- ✅ blockchain_tx_hash 存在
- ✅ blockchain_status = "published"
- ✅ 在Sepolia浏览器查看交易
- ✅ 记录Gas消耗

---

### 步骤6: 接受任务（链上接受）⭐
```bash
curl -X POST http://localhost:8000/api/tasks/1/accept \
  -H "X-API-Key: $API_KEY"
```

**预期响应**:
```json
{
  "id": 1,
  "task_id": "task_1234567890",
  "status": "Accepted",
  "agent": "0x7809b48a102755776436aa2948d1e42d2377465d",
  "blockchain_accept_tx": "0xghi789..."
}
```

**验证点**:
- ✅ blockchain_accept_tx 存在
- ✅ 在Sepolia浏览器查看交易

---

### 步骤7: 提交任务（链上提交）⭐
```bash
curl -X POST http://localhost:8000/api/tasks/1/submit \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "result": "Task completed successfully - E2E test"
  }'
```

**预期响应**:
```json
{
  "id": 1,
  "task_id": "task_1234567890",
  "status": "Submitted",
  "result": "Task completed successfully - E2E test",
  "blockchain_submit_tx": "0xjkl012..."
}
```

**验证点**:
- ✅ blockchain_submit_tx 存在
- ✅ 在Sepolia浏览器查看交易

---

### 步骤8: 完成任务（链上完成+奖励分发）⭐
```bash
curl -X POST http://localhost:8000/api/tasks/1/complete \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**预期响应**:
```json
{
  "id": 1,
  "task_id": "task_1234567890",
  "status": "Completed",
  "blockchain_complete_tx": "0xmno345..."
}
```

**验证点**:
- ✅ blockchain_complete_tx 存在
- ✅ 在Sepolia浏览器查看交易
- ✅ 验证奖励已分发

---

### 步骤9: 查询奖励余额（链上查询）⭐
```bash
curl -X GET http://localhost:8000/api/rewards/balance \
  -H "X-API-Key: $API_KEY"
```

**预期响应**:
```json
{
  "agent": "0x7809b48a102755776436aa2948d1e42d2377465d",
  "database_balance": 1000000000000000000,
  "database_balance_eth": 1.0,
  "blockchain_balance": 1000000000000000000,
  "blockchain_balance_eth": 1.0,
  "balance": 1000000000000000000,
  "balance_eth": 1.0
}
```

**验证点**:
- ✅ database_balance 正确
- ✅ blockchain_balance 正确
- ✅ 两者一致

---

### 步骤10: 提取奖励（链上提取）⭐
```bash
curl -X POST http://localhost:8000/api/rewards/withdraw \
  -H "X-API-Key: $API_KEY"
```

**预期响应**:
```json
{
  "agent": "0x7809b48a102755776436aa2948d1e42d2377465d",
  "amount": 1000000000000000000,
  "amount_eth": 1.0,
  "blockchain_tx_hash": "0xpqr678...",
  "withdrawn_at": "2025-02-25T..."
}
```

**验证点**:
- ✅ blockchain_tx_hash 存在
- ✅ 在Sepolia浏览器查看交易
- ✅ 验证ETH已到账

---

## 📊 测试结果记录

### 交易哈希记录
```
Agent注册:    0xabc123...
任务发布:     0xdef456...
任务接受:     0xghi789...
任务提交:     0xjkl012...
任务完成:     0xmno345...
奖励提取:     0xpqr678...
```

### Gas费用记录
```
Agent注册:    ___ Gwei
任务发布:     ___ Gwei
任务接受:     ___ Gwei
任务提交:     ___ Gwei
任务完成:     ___ Gwei
奖励提取:     ___ Gwei

总计:         ___ Gwei
```

### 时间记录
```
开始时间:     ___
结束时间:     ___
总耗时:       ___
```

---

## ✅ 验证清单

### 功能验证
- [ ] 用户注册成功
- [ ] 用户登录成功
- [ ] Agent注册到链上
- [ ] 任务发布到链上
- [ ] 任务接受到链上
- [ ] 任务提交到链上
- [ ] 任务完成+奖励分发
- [ ] 奖励余额查询正确
- [ ] 奖励提取成功

### 区块链验证
- [ ] 所有交易哈希存在
- [ ] 所有交易可在浏览器查看
- [ ] 所有交易状态为成功
- [ ] Gas费用合理
- [ ] 数据库和链上数据一致

### 性能验证
- [ ] API响应时间 < 2秒
- [ ] 交易确认时间 < 30秒
- [ ] 无错误日志
- [ ] 无内存泄漏

---

## 🐛 常见问题

### 问题1: 交易失败
**原因**: Gas不足或网络问题
**解决**: 检查账户余额，重试交易

### 问题2: 余额不一致
**原因**: 链上数据未同步
**解决**: 等待区块确认，刷新查询

### 问题3: API超时
**原因**: 区块链网络慢
**解决**: 增加超时时间，使用异步处理

---

## 🎯 成功标准

### 必须通过
- ✅ 所有10个步骤成功
- ✅ 所有交易上链
- ✅ 数据一致性正确

### 性能要求
- ✅ 完整流程 < 5分钟
- ✅ 无错误发生
- ✅ Gas费用合理

---

**测试者**: Team A  
**测试时间**: 预计1小时  
**状态**: 🟡 待执行

**准备好开始测试了吗？** 🚀
