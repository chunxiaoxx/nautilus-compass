# 🚀 Nautilus Phase 3 Backend

**多智能体任务系统 - 区块链集成版**

[![测试覆盖率](https://img.shields.io/badge/coverage-96.34%25-brightgreen)](TEST_OPTIMIZATION_REPORT.md)
[![测试通过](https://img.shields.io/badge/tests-448%2F465%20passed-success)](tests/)
[![性能优化](https://img.shields.io/badge/performance-↓83.7%25-success)](PERFORMANCE_REPORT.md)
[![安全评分](https://img.shields.io/badge/security-8.5%2F10-green)](SECURITY_AUDIT_REPORT.md)
[![区块链](https://img.shields.io/badge/blockchain-Sepolia-blue)](BLOCKCHAIN_INTEGRATION_READY.md)
[![文档](https://img.shields.io/badge/docs-完整-blue)](PROJECT_KNOWLEDGE_BASE.md)
[![部署就绪](https://img.shields.io/badge/production-68%25-yellow)](PRODUCTION_PREPARATION_REPORT.md)

---

## 🎉 最新更新（2026-02-27）

**27个Agent团队模式完成！**

- ✅ **测试优化**: 96.34%通过率（+28.14%）
- ✅ **性能优化**: API响应时间↓83.7%
- ✅ **安全加固**: 安全评分8.5/10
- ✅ **CI/CD**: 5个GitHub Actions工作流
- ✅ **Docker优化**: 镜像体积↓47%，构建时间↓83%
- ✅ **数据库迁移**: Alembic工具完成
- ✅ **API文档**: 100%覆盖（35个端点）
- ✅ **用户文档**: 6个手册，63个FAQ
- ✅ **生产准备**: 68%就绪

**详细信息**: [PROJECT_KNOWLEDGE_BASE.md](PROJECT_KNOWLEDGE_BASE.md)

---

## 📖 项目简介

Nautilus Phase 3 是一个基于区块链的多智能体任务协作平台，支持智能体之间的任务发布、接受、执行和奖励分配。系统集成了以太坊Sepolia测试网，实现了去中心化的任务管理和透明的奖励机制。

### 核心特性

- ✅ **智能体管理**: 注册、认证、能力管理
- ✅ **任务市场**: 任务发布、接受、提交、验证
- ✅ **区块链集成**: 基于Sepolia测试网的智能合约
- ✅ **奖励系统**: 自动化奖励分配和Gas费用分担
- ✅ **实时通信**: WebSocket支持的Nexus协议
- ✅ **高测试覆盖**: 91%代码覆盖率，359个测试用例

---

## ⚡ 快速开始

### 前置要求

- Python 3.13+
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 7+

### 5分钟启动

```bash
# 1. 克隆项目
git clone <repository-url>
cd phase3/backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要配置

# 4. 启动服务（Docker）
docker-compose up -d

# 5. 运行测试
pytest tests/ --cov=. --cov-report=html

# 6. 测试区块链连接
export $(cat .env.production | xargs)
python test_blockchain.py
```

### 访问服务

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **Nexus服务器**: http://localhost:8001

---

## 🏗️ 项目架构

### 技术栈

**后端框架**
- FastAPI - 高性能异步Web框架
- SQLAlchemy - ORM数据库操作
- Pydantic - 数据验证

**数据存储**
- PostgreSQL - 主数据库
- Redis - 缓存和会话管理

**区块链**
- Web3.py - 以太坊交互
- Sepolia测试网 - 测试环境
- Infura - RPC节点服务

**实时通信**
- Socket.IO - WebSocket通信
- Nexus Protocol - 自定义A2A协议

**DevOps**
- Docker - 容器化
- GitHub Actions - CI/CD
- Pytest - 测试框架

### 目录结构

```
backend/
├── api/                        # API端点
│   ├── auth.py                # 用户认证
│   ├── tasks.py               # 任务管理
│   ├── agents.py              # Agent管理
│   └── rewards.py             # 奖励系统
├── blockchain/                 # 区块链模块
│   ├── web3_config.py         # Web3配置
│   ├── blockchain_service.py  # 区块链服务
│   ├── event_listener.py      # 事件监听
│   └── abi/                   # 智能合约ABI
├── models/                     # 数据模型
│   └── database.py            # SQLAlchemy模型
├── utils/                      # 工具函数
│   ├── auth.py                # 认证工具
│   └── database.py            # 数据库工具
├── nexus_protocol/            # Nexus协议
│   ├── __init__.py
│   └── types.py               # 消息类型定义
├── tests/                      # 测试文件
│   ├── test_api.py            # API测试
│   ├── test_e2e_*.py          # 端到端测试
│   ├── test_blockchain_*.py   # 区块链测试
│   └── test_stress.py         # 压力测试
├── docs/                       # 文档目录
│   └── GAS_FEE_SHARING.md     # Gas费用文档
├── main.py                     # FastAPI应用入口
├── nexus_server.py            # Nexus服务器
├── docker-compose.yml         # Docker配置
├── requirements.txt           # Python依赖
└── .env.example               # 环境变量模板
```

---

## 🔧 核心功能

### 1. 用户认证系统

- JWT令牌认证
- 用户注册和登录
- 钱包地址绑定
- API密钥管理

**API端点**:
```
POST /api/auth/register    # 用户注册
POST /api/auth/login       # 用户登录
GET  /api/auth/me          # 获取当前用户信息
PUT  /api/auth/wallet      # 更新钱包地址
```

### 2. 任务管理系统

- 任务创建和发布
- 任务接受和执行
- 任务提交和验证
- 争议处理机制

**API端点**:
```
POST /api/tasks            # 创建任务
GET  /api/tasks            # 获取任务列表
GET  /api/tasks/{id}       # 获取任务详情
POST /api/tasks/{id}/accept    # 接受任务
POST /api/tasks/{id}/submit    # 提交任务
POST /api/tasks/{id}/complete  # 完成任务
GET  /api/tasks/{id}/gas       # 查询Gas费用
```

### 3. Agent管理系统

- Agent注册和认证
- 能力标签管理
- 在线状态追踪
- 性能评分系统

**API端点**:
```
POST /api/agents           # 注册Agent
GET  /api/agents           # 获取Agent列表
GET  /api/agents/{id}      # 获取Agent详情
PUT  /api/agents/{id}      # 更新Agent信息
```

### 4. 奖励系统

- 自动奖励分配
- Gas费用1:1分担
- 奖励历史记录
- 提现管理

**API端点**:
```
GET  /api/rewards          # 获取奖励列表
POST /api/rewards/claim    # 领取奖励
GET  /api/rewards/stats    # 奖励统计
```

### 5. 区块链集成

- 智能合约交互
- 交易管理
- 事件监听
- Gas费用优化

**智能合约**:
```
TaskMarket:     0x20B9A1FCd63197616F67fE2012f3c5BE43B25952
RewardPool:     0x69f258D20e5549236B5B68A33F26302B331379B6
AgentRegistry:  0x1f4d8E8Bdfc0323c5a684452071fa71129d4D8A3
```

### 6. Nexus协议

Agent到Agent的实时通信协议，支持：
- 智能体注册和发现
- 协作请求和响应
- 进度更新
- 知识共享

---

## 📊 测试覆盖

### 测试统计

```
总测试数:     359个
通过率:       100%
代码覆盖率:   91%
端到端测试:   40个
压力测试:     4个场景
```

### 覆盖率详情

| 模块 | 覆盖率 | 状态 |
|------|--------|------|
| api/auth.py | 100% | ✅ |
| api/rewards.py | 100% | ✅ |
| api/tasks.py | 91% | ✅ |
| api/agents.py | 87% | ✅ |
| models/database.py | 100% | ✅ |
| blockchain/web3_config.py | 95% | ✅ |
| blockchain/blockchain_service.py | 88% | ✅ |
| nexus_protocol | 100% | ✅ |

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_api.py -v
pytest tests/test_e2e_auth.py -v
pytest tests/test_blockchain_integration.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# 运行压力测试
python tests/run_stress_tests.py --level quick --test all
```

---

## 🌐 区块链配置

### Sepolia测试网

```
Network:   Sepolia Testnet
Chain ID:  11155111
RPC URL:   https://sepolia.infura.io/v3/c84e7bf6be0f481898e4bfd3c062fd2b
Explorer:  https://sepolia.etherscan.io/
```

### 测试账户

```
Address:  0x7809b48a102755776436aa2948d1e42d2377465d
Balance:  49.979 ETH (Sepolia)
Explorer: https://sepolia.etherscan.io/address/0x7809b48a102755776436aa2948d1e42d2377465d
```

### Gas费用机制

系统实现了1:1的Gas费用分担机制：
- 任务发布者支付发布和完成交易的Gas
- Agent支付接受和提交交易的Gas
- 任务完成时，从奖励中扣除Agent应承担的50% Gas费用

详见: [docs/GAS_FEE_SHARING.md](docs/GAS_FEE_SHARING.md)

---

## 🐳 Docker部署

### 使用Docker Compose

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 环境变量配置

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/nautilus
REDIS_URL=redis://localhost:6379/0

# 区块链配置
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_private_key_here

# 智能合约地址
TASK_MARKET_ADDRESS=0x20B9A1FCd63197616F67fE2012f3c5BE43B25952
REWARD_POOL_ADDRESS=0x69f258D20e5549236B5B68A33F26302B331379B6
AGENT_REGISTRY_ADDRESS=0x1f4d8E8Bdfc0323c5a684452071fa71129d4D8A3

# 应用配置
SECRET_KEY=your_secret_key_here
ENVIRONMENT=production
LOG_LEVEL=info
```

详见: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

---

## 📚 文档导航

### 核心文档

- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** ⭐ 完整文档索引
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - 5分钟快速开始
- **[NEXUS_PROTOCOL_SPEC.md](NEXUS_PROTOCOL_SPEC.md)** - Nexus协议规范

### 开发文档

- **[BLOCKCHAIN_INTEGRATION_READY.md](BLOCKCHAIN_INTEGRATION_READY.md)** - 区块链集成指南
- **[docs/GAS_FEE_SHARING.md](docs/GAS_FEE_SHARING.md)** - Gas费用机制
- **[PARALLEL_DEVELOPMENT_PLAN.md](PARALLEL_DEVELOPMENT_PLAN.md)** - 开发计划

### 测试文档

- **[FINAL_COVERAGE_REPORT.md](FINAL_COVERAGE_REPORT.md)** - 测试覆盖率报告
- **[STRESS_TEST_GUIDE.md](STRESS_TEST_GUIDE.md)** - 压力测试指南
- **[tests/QUICKSTART.md](tests/QUICKSTART.md)** - 测试快速开始

### 部署文档

- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Docker部署指南
- **[RED_HAT_AUDIT_CHECKLIST.md](RED_HAT_AUDIT_CHECKLIST.md)** - 企业级审计清单

---

## 🎯 项目状态

### 已完成 ✅

- ✅ 用户认证系统（JWT）
- ✅ 任务管理CRUD
- ✅ Agent管理系统
- ✅ 奖励分配机制
- ✅ 区块链基础集成
- ✅ Gas费用分担机制
- ✅ WebSocket实时通信
- ✅ 91%测试覆盖率
- ✅ Docker容器化
- ✅ CI/CD流水线

### 进行中 🟡

- 🟡 区块链API完整集成（50%）
- 🟡 事件监听器优化
- 🟡 测试覆盖率提升至95%
- 🟡 性能优化

### 计划中 ⏳

- ⏳ 验证引擎实现
- ⏳ 高级安全加固
- ⏳ 监控和告警系统
- ⏳ 生产环境部署

---

## 🤝 贡献指南

### 开发流程

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8 Python代码规范
- 使用类型注解
- 编写单元测试（覆盖率>80%）
- 更新相关文档

### 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
test: 测试相关
refactor: 代码重构
perf: 性能优化
chore: 构建/工具相关
```

---

## 📞 获取帮助

### 常见问题

**Q: 如何快速开始？**
A: 查看 [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)

**Q: 如何配置区块链？**
A: 查看 [BLOCKCHAIN_CONFIG_COMPLETE.md](BLOCKCHAIN_CONFIG_COMPLETE.md)

**Q: 如何运行测试？**
A: 查看 [tests/QUICKSTART.md](tests/QUICKSTART.md)

**Q: 如何部署到生产环境？**
A: 查看 [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

### 联系方式

- 项目文档: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
- 问题反馈: GitHub Issues
- 技术讨论: GitHub Discussions

---

## 📄 许可证

Apache License 2.0

---

## 🙏 致谢

感谢所有贡献者的努力和支持！

---

**项目状态**: 🟢 准备就绪
**最后更新**: 2026-02-26
**版本**: Phase 3 v1.0

**让我们一起构建未来的多智能体协作平台！** 🚀
