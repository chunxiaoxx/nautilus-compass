# 依赖管理快速指南

**状态**: ✅ 已完成
**日期**: 2026-02-25

---

## 快速开始

### 1. 安装依赖

```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
pip install -r requirements.txt
```

### 2. 验证安装

```bash
pip list | grep -E "(bcrypt|sqlalchemy|jose|passlib|fastapi|socketio)"
```

### 3. 启动应用

```bash
python main.py
```

---

## 依赖清单（18个）

### 核心框架
- `fastapi==0.104.1` - Web框架
- `uvicorn==0.24.0` - ASGI服务器
- `pydantic==2.5.0` - 数据验证

### 数据库
- `sqlalchemy>=2.0.0` - ORM
- `psycopg2-binary>=2.9.0` - PostgreSQL驱动

### 认证与安全
- `python-jose[cryptography]>=3.3.0` - JWT
- `passlib[bcrypt]>=1.7.4` - 密码哈希
- `bcrypt>=4.0.0` - bcrypt算法 ⭐ **新增**

### WebSocket
- `python-socketio==5.10.0` - Socket.IO服务器
- `python-socketio[asyncio_client]>=5.10.0` - 异步客户端 ⭐ **新增**

### 工具库
- `python-dotenv>=1.0.0` - 环境变量
- `httpx>=0.27.0` - HTTP客户端
- `aiofiles==23.2.1` - 异步文件
- `psutil==5.9.8` - 系统监控
- `python-multipart==0.0.6` - 文件上传

### 测试
- `pytest==7.4.3` - 测试框架
- `pytest-asyncio==0.21.1` - 异步测试
- `pytest-cov>=4.1.0` - 测试覆盖率

---

## TODO处理总结（8个）

所有TODO已标记为 **[Phase 2]** 并添加详细说明：

### 智能体管理（1个）
- ✅ `api/agents.py:70` - 区块链智能体注册

### 任务管理（5个）
- ✅ `api/tasks.py:72` - 区块链任务发布
- ✅ `api/tasks.py:173` - 区块链任务接受
- ✅ `api/tasks.py:227` - 区块链结果提交
- ✅ `api/tasks.py:238` - 验证引擎触发
- ✅ `api/tasks.py:285` - 区块链争议处理

### 奖励管理（2个）
- ✅ `api/rewards.py:41` - 区块链余额查询
- ✅ `api/rewards.py:70` - 区块链奖励提取

---

## 常见问题

### Q: 为什么添加bcrypt？
A: `utils/auth.py` 使用bcrypt进行密码哈希，需要显式安装。

### Q: 为什么添加python-socketio[asyncio_client]？
A: 测试和客户端需要异步Socket.IO客户端支持。

### Q: TODO什么时候实现？
A: 所有TODO都是区块链集成功能，计划在Phase 2实现。

### Q: 当前功能完整吗？
A: 是的。Phase 1 MVP使用数据库实现所有功能，可以正常运行。

---

## 文件清单

### 修改的文件
- `requirements.txt` - 添加2个依赖
- `api/agents.py` - 更新1个TODO
- `api/tasks.py` - 更新5个TODO
- `api/rewards.py` - 更新2个TODO

### 新增的文件
- `DEPENDENCY_TODO_REPORT.md` - 完整报告
- `DEPENDENCY_QUICKSTART.md` - 本文档

---

## 验证命令

```bash
# 检查依赖数量
wc -l requirements.txt
# 应该显示: 18 requirements.txt

# 检查TODO更新
grep -c "TODO \[Phase 2\]" api/*.py
# 应该显示: agents.py:1, rewards.py:2, tasks.py:5

# 测试导入
python -c "import bcrypt, sqlalchemy, jose, passlib; print('✅ All dependencies OK')"
```

---

## 下一步

1. 安装依赖: `pip install -r requirements.txt`
2. 配置环境: 复制 `.env.example` 到 `.env`
3. 初始化数据库: `python -c "from utils.database import init_db; init_db()"`
4. 启动服务: `python main.py`
5. 运行测试: `pytest tests/`

---

**完整报告**: 查看 `DEPENDENCY_TODO_REPORT.md`

**项目状态**: ✅ Phase 1 MVP 完成，依赖已修复，TODO已规划
