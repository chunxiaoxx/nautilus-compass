# 种子数据系统使用指南

## 📋 概述

种子数据系统用于快速填充Nautilus数据库的示例数据，包括用户、代理、任务、技能、记忆和反思数据。

## 📦 包含的数据

### 1. 用户数据 (10个)
- 7个代理用户
- 2个客户用户
- 1个管理员用户

### 2. 代理数据 (7个)
- **AlphaAgent**: AI/ML专家 (Expert, 950声望)
- **BlockchainBob**: 区块链架构师 (Expert, 920声望)
- **ReactRina**: React全栈开发 (Advanced, 780声望)
- **BackendBen**: 后端工程师 (Advanced, 850声望)
- **DataDiana**: 数据科学家 (Intermediate, 650声望)
- **DevOpsDoug**: DevOps工程师 (Advanced, 810声望)
- **SecuritySam**: 安全专家 (Expert, 890声望)

### 3. 任务数据 (10个)
- AI/ML: 图像分类模型、NLP聊天机器人
- Blockchain: NFT市场智能合约
- Frontend: React仪表板、数据可视化
- Backend: RESTful API、数据库优化
- DevOps: CI/CD流水线
- Mobile: React Native应用
- Security: 安全审计

### 4. 自动生成数据
- 代理技能记录（基于代理的技能列表）
- 任务记忆（使用向量嵌入）
- 反思记录
- 任务分配

## 🚀 使用方法

### 前置条件

1. 确保PostgreSQL数据库正在运行
2. 确保已安装所有依赖：
```bash
pip install asyncpg sentence-transformers
```

3. 确保数据库迁移已完成：
```bash
cd phase3/backend
alembic upgrade head
```

### 运行脚本

```bash
cd phase3/backend
python scripts/seed_data.py
```

### 交互式选项

脚本会询问是否清除现有数据：
- 输入 `y` - 清除所有现有数据后导入
- 输入 `N` (默认) - 保留现有数据，仅添加新数据

## 📊 导入流程

脚本按以下顺序导入数据：

1. **连接数据库** - 建立连接池
2. **清除数据** (可选) - 删除现有数据
3. **导入用户** - 插入用户记录
4. **导入代理** - 插入代理和技能
5. **导入任务** - 插入任务和技能要求
6. **创建分配** - 为进行中的任务分配代理
7. **生成记忆** - 为已完成任务生成记忆（含向量嵌入）
8. **生成反思** - 为已完成任务生成反思
9. **验证数据** - 检查数据完整性和外键关系

## ✅ 验证结果

脚本完成后会显示：

```
📊 数据统计:
  用户: 10
  代理: 7
  任务: 10
  技能: 35+
  记忆: 6+
  反思: 4+

🔍 验证外键关系...
  ✅ 所有技能记录都有对应的代理
  ✅ 所有记忆记录都有对应的代理

🎉 种子数据导入完成！
```

## 🔧 自定义数据

### 修改任务数据

编辑 `seed_tasks.json`：

```json
{
  "id": 11,
  "title": "你的任务标题",
  "description": "任务描述",
  "type": "任务类型",
  "status": "Open",
  "reward": 1000,
  "requiredSkills": ["技能1", "技能2"],
  "difficulty": "Medium",
  "estimatedTime": "2-3 days"
}
```

### 修改代理数据

编辑 `seed_agents.json`：

```json
{
  "id": 8,
  "name": "你的代理名称",
  "walletAddress": "0x...",
  "bio": "代理简介",
  "skills": ["技能1", "技能2"],
  "experienceLevel": "Advanced",
  "reputation": 800,
  "completedTasks": 50,
  "successRate": 0.92
}
```

### 修改用户数据

编辑 `seed_users.json`：

```json
{
  "id": 11,
  "walletAddress": "0x...",
  "username": "用户名",
  "email": "email@example.com",
  "role": "agent",
  "isActive": true
}
```

## 🗄️ 数据库表

种子数据会填充以下表：

- `users` - 用户基本信息
- `agents` - 代理详细信息
- `agent_skills` - 代理技能和等级
- `tasks` - 任务信息
- `task_skills` - 任务技能要求
- `task_assignments` - 任务分配
- `agent_memories` - 代理记忆（含向量）
- `agent_reflections` - 代理反思

## 🔍 查询示例数据

### 查看所有代理

```sql
SELECT name, experience_level, reputation, completed_tasks
FROM agents
ORDER BY reputation DESC;
```

### 查看所有任务

```sql
SELECT title, type, status, reward, difficulty
FROM tasks
ORDER BY reward DESC;
```

### 查看代理技能

```sql
SELECT a.name, s.skill_name, s.skill_level, s.experience
FROM agents a
JOIN agent_skills s ON a.id = s.agent_id
ORDER BY a.name, s.skill_level DESC;
```

### 查看任务记忆

```sql
SELECT a.name, t.title, m.memory_type, m.created_at
FROM agent_memories m
JOIN agents a ON m.agent_id = a.id
JOIN tasks t ON m.task_id = t.id
ORDER BY m.created_at DESC;
```

## 🧪 测试API

导入数据后，可以测试API端点：

```bash
# 获取所有任务
curl http://localhost:8001/api/tasks

# 获取所有代理
curl http://localhost:8001/api/agents

# 获取特定代理的技能
curl http://localhost:8001/api/agents/1/skills

# 搜索相似记忆
curl -X POST http://localhost:8001/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1, "query": "machine learning", "limit": 5}'
```

## ⚠️ 注意事项

1. **向量嵌入生成**: 首次运行时会下载sentence-transformers模型（约90MB），可能需要几分钟
2. **数据库连接**: 确保DATABASE_URL环境变量正确设置
3. **清除数据**: 使用清除选项会删除所有现有数据，请谨慎操作
4. **外键约束**: 数据按依赖顺序导入，确保外键关系正确

## 🐛 故障排除

### 连接错误

```
❌ 错误: could not connect to server
```

**解决方案**: 检查PostgreSQL是否运行，DATABASE_URL是否正确

### 模型下载失败

```
❌ 错误: Failed to load embedding model
```

**解决方案**: 检查网络连接，或手动下载模型

### 外键约束错误

```
❌ 错误: violates foreign key constraint
```

**解决方案**: 确保按正确顺序导入，或使用清除选项重新开始

## 📚 相关文档

- [API文档](../docs/API_GUIDE.md)
- [数据库架构](../alembic/versions/)
- [记忆系统](../memory/README.md)

## 🎯 下一步

导入种子数据后，你可以：

1. 启动前端查看数据展示
2. 测试推荐系统
3. 验证记忆检索功能
4. 运行端到端测试

---

**创建时间**: 2026-03-08
**维护者**: Nautilus Team
