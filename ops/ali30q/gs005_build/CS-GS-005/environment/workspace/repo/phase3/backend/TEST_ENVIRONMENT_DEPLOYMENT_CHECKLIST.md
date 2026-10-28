# Nautilus Phase 3 Backend - 测试环境部署检查清单

**生成日期**: 2026-02-26
**环境**: 测试环境 (Test Environment)
**网络**: Sepolia 测试网

---

## 📋 部署前检查清单

### 1. 系统环境检查

- [ ] **操作系统**: Linux/Unix 系统（推荐 Ubuntu 20.04+）
- [ ] **Python 版本**: Python 3.9+ 已安装
- [ ] **Docker**: Docker 20.10+ 已安装（如使用容器部署）
- [ ] **Docker Compose**: Docker Compose 1.29+ 已安装
- [ ] **Git**: Git 已安装
- [ ] **磁盘空间**: 至少 20GB 可用空间
- [ ] **内存**: 至少 4GB RAM
- [ ] **CPU**: 至少 2 核心

### 2. 依赖服务检查

- [ ] **PostgreSQL**:
  - 版本 13+ 已安装并运行
  - 数据库 `nautilus_test` 已创建
  - 用户 `nautilus_test` 已创建并授权
  - 连接测试通过

- [ ] **Redis**:
  - 版本 6+ 已安装并运行
  - 密码已设置
  - 连接测试通过

- [ ] **区块链节点访问**:
  - Infura/Alchemy 账户已创建
  - API Key 已获取
  - Sepolia RPC 连接测试通过

### 3. 配置文件检查

- [ ] **.env.test 文件**:
  - 已从 .env.production.example 复制
  - 所有必需的环境变量已配置
  - 密钥已生成并替换
  - 数据库连接字符串正确
  - Redis 连接字符串正确
  - 区块链配置正确

- [ ] **密钥生成**:
  - JWT_SECRET_KEY 已生成
  - CSRF_SECRET_KEY 已生成
  - REDIS_PASSWORD 已生成
  - 数据库密码已生成

### 4. 区块链配置检查

- [ ] **网络配置**:
  - BLOCKCHAIN_NETWORK=sepolia
  - Sepolia RPC URL 已配置
  - Infura Project ID 已填入

- [ ] **智能合约部署**:
  - 合约已部署到 Sepolia 测试网
  - 所有合约地址已记录
  - 合约地址已填入 .env.test

- [ ] **测试账户**:
  - 测试账户已创建
  - 账户地址已填入配置
  - 账户有足够的 Sepolia ETH（从水龙头获取）
  - 私钥已安全存储

### 5. 安全配置检查

- [ ] **私钥管理**:
  - 私钥管理方式已选择（加密文件/KMS）
  - 加密密钥已设置
  - 私钥文件权限正确（600）

- [ ] **CORS 配置**:
  - 允许的域名已配置
  - 不使用通配符 *

- [ ] **速率限制**:
  - 速率限制已启用
  - 限制值适合测试环境

- [ ] **HTTPS**:
  - 测试环境可使用 HTTP
  - 如使用 HTTPS，证书已配置

### 6. 日志和监控检查

- [ ] **日志目录**:
  - /var/log/nautilus 目录已创建
  - 目录权限正确（应用可写入）

- [ ] **备份目录**:
  - /var/backups/nautilus/test 目录已创建
  - 目录权限正确

- [ ] **监控配置**:
  - Prometheus 端口可访问（如启用）
  - 健康检查端点可访问

### 7. 网络和防火墙检查

- [ ] **端口开放**:
  - 8000 (API 端口)
  - 8001 (Nexus 端口)
  - 5432 (PostgreSQL，如远程访问)
  - 6379 (Redis，如远程访问)
  - 9090 (Prometheus，如启用)

- [ ] **网络连通性**:
  - 应用服务器可访问数据库
  - 应用服务器可访问 Redis
  - 应用服务器可访问外部 RPC 节点
  - 前端可访问后端 API

### 8. 代码和依赖检查

- [ ] **代码仓库**:
  - 最新代码已拉取
  - 分支正确（test/staging）

- [ ] **Python 依赖**:
  - requirements.txt 存在
  - 虚拟环境已创建
  - 依赖已安装

- [ ] **数据库迁移**:
  - 迁移脚本已准备
  - 迁移测试通过

---

## 🚀 部署步骤

### 步骤 1: 准备环境

```bash
# 1.1 克隆代码（如未克隆）
git clone <repository-url>
cd nautilus-core/phase3/backend

# 1.2 切换到测试分支
git checkout test

# 1.3 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 1.4 安装依赖
pip install -r requirements.txt
```

### 步骤 2: 配置环境变量

```bash
# 2.1 复制配置文件
cp .env.production.example .env.test

# 2.2 生成密钥
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('CSRF_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(24))"
python -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(24))"

# 2.3 编辑 .env.test 文件
nano .env.test
# 填入生成的密钥和其他配置
```

### 步骤 3: 准备数据库

```bash
# 3.1 创建数据库
sudo -u postgres psql
CREATE DATABASE nautilus_test;
CREATE USER nautilus_test WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE nautilus_test TO nautilus_test;
\q

# 3.2 运行数据库迁移
python manage.py migrate

# 3.3 创建超级用户（可选）
python manage.py createsuperuser
```

### 步骤 4: 配置区块链

```bash
# 4.1 部署智能合约到 Sepolia
cd contracts
npx hardhat deploy --network sepolia

# 4.2 记录合约地址
# 将合约地址填入 .env.test

# 4.3 验证合约部署
npx hardhat verify --network sepolia <contract-address>
```

### 步骤 5: 配置私钥管理

```bash
# 5.1 创建密钥目录
mkdir -p keys
chmod 700 keys

# 5.2 生成加密密钥文件（如使用加密文件方式）
python scripts/generate_encrypted_key.py \
  --private-key <your-private-key> \
  --output keys/test_encrypted_key.json \
  --password <encryption-password>

# 5.3 设置文件权限
chmod 600 keys/test_encrypted_key.json
```

### 步骤 6: 启动服务

#### 方式 A: 直接运行

```bash
# 6.1 启动应用
export ENV_FILE=.env.test
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --env-file .env.test
```

#### 方式 B: 使用 Docker

```bash
# 6.1 构建镜像
docker build -t nautilus-backend:test .

# 6.2 启动容器
docker-compose -f docker-compose.test.yml up -d

# 6.3 查看日志
docker-compose -f docker-compose.test.yml logs -f
```

### 步骤 7: 验证部署

```bash
# 7.1 健康检查
curl http://localhost:8000/health

# 7.2 API 文档访问
curl http://localhost:8000/docs

# 7.3 测试 API 端点
curl http://localhost:8000/api/v1/status

# 7.4 测试区块链连接
curl http://localhost:8000/api/v1/blockchain/status
```

---

## ✅ 部署后验证

### 1. 服务状态验证

- [ ] **应用服务**:
  - 进程正在运行
  - 端口 8000 和 8001 正在监听
  - 健康检查返回 200 OK

- [ ] **数据库连接**:
  - 数据库连接池正常
  - 可以执行查询

- [ ] **Redis 连接**:
  - Redis 连接正常
  - 可以读写缓存

- [ ] **区块链连接**:
  - RPC 连接正常
  - 可以查询区块高度
  - 可以查询账户余额

### 2. 功能验证

- [ ] **用户认证**:
  - 注册功能正常
  - 登录功能正常
  - JWT Token 生成正常

- [ ] **API 端点**:
  - 所有 API 端点响应正常
  - 错误处理正确
  - 速率限制生效

- [ ] **区块链交互**:
  - 可以读取合约状态
  - 可以发送交易（测试网）
  - 事件监听正常

- [ ] **WebSocket**:
  - WebSocket 连接正常
  - 消息推送正常

### 3. 性能验证

- [ ] **响应时间**:
  - API 响应时间 < 200ms
  - 数据库查询时间 < 100ms

- [ ] **并发测试**:
  - 可以处理 50+ 并发请求
  - 无内存泄漏

- [ ] **资源使用**:
  - CPU 使用率 < 70%
  - 内存使用率 < 80%
  - 磁盘 I/O 正常

### 4. 安全验证

- [ ] **认证授权**:
  - 未授权请求被拒绝
  - Token 过期处理正确
  - CSRF 保护生效

- [ ] **速率限制**:
  - 超过限制返回 429
  - 限制按预期工作

- [ ] **输入验证**:
  - SQL 注入防护
  - XSS 防护
  - 参数验证正确

### 5. 日志和监控验证

- [ ] **日志记录**:
  - 日志文件正常写入
  - 日志格式正确
  - 日志轮转正常

- [ ] **错误追踪**:
  - 错误被正确记录
  - 堆栈信息完整

- [ ] **监控指标**:
  - Prometheus 指标可访问
  - 关键指标正常

---

## 🔧 故障排查

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查数据库服务
sudo systemctl status postgresql

# 检查连接
psql -U nautilus_test -d nautilus_test -h localhost

# 检查配置
grep DATABASE_URL .env.test
```

#### 2. Redis 连接失败

```bash
# 检查 Redis 服务
sudo systemctl status redis

# 测试连接
redis-cli -a <password> ping

# 检查配置
grep REDIS .env.test
```

#### 3. 区块链 RPC 连接失败

```bash
# 测试 RPC 连接
curl -X POST https://sepolia.infura.io/v3/<project-id> \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# 检查配置
grep BLOCKCHAIN_RPC_URL .env.test
```

#### 4. 端口被占用

```bash
# 查看端口占用
sudo netstat -tulpn | grep 8000
sudo lsof -i :8000

# 停止占用进程
sudo kill -9 <PID>
```

#### 5. 权限问题

```bash
# 检查日志目录权限
ls -la /var/log/nautilus

# 修复权限
sudo chown -R <app-user>:<app-group> /var/log/nautilus
sudo chmod 755 /var/log/nautilus
```

---

## 📊 部署验证报告模板

```
部署验证报告
================

部署日期: _______________
部署人员: _______________
环境: 测试环境

系统检查:
- [ ] 操作系统: _______________
- [ ] Python 版本: _______________
- [ ] Docker 版本: _______________

服务状态:
- [ ] 应用服务: 运行中 / 停止
- [ ] PostgreSQL: 运行中 / 停止
- [ ] Redis: 运行中 / 停止

配置验证:
- [ ] 环境变量: 完整 / 缺失
- [ ] 密钥生成: 完成 / 未完成
- [ ] 区块链配置: 正确 / 错误

功能测试:
- [ ] 健康检查: 通过 / 失败
- [ ] API 端点: 通过 / 失败
- [ ] 区块链连接: 通过 / 失败
- [ ] 数据库操作: 通过 / 失败

性能指标:
- API 响应时间: _____ ms
- 并发处理能力: _____ req/s
- CPU 使用率: _____ %
- 内存使用率: _____ %

问题记录:
1. _______________
2. _______________

备注:
_______________

签名: _______________
```

---

## 📝 回滚计划

如果部署失败，按以下步骤回滚：

### 1. 停止服务

```bash
# Docker 方式
docker-compose -f docker-compose.test.yml down

# 直接运行方式
pkill -f "python main.py"
```

### 2. 恢复数据库

```bash
# 从备份恢复
pg_restore -U nautilus_test -d nautilus_test /var/backups/nautilus/test/latest.dump
```

### 3. 恢复代码

```bash
# 切换到上一个稳定版本
git checkout <previous-stable-tag>
```

### 4. 重启服务

```bash
# 使用之前的配置重启
docker-compose -f docker-compose.test.yml up -d
```

---

## 📞 联系信息

**技术支持**: tech-support@nautilus.local
**运维团队**: ops@nautilus.local
**紧急联系**: emergency@nautilus.local

---

**检查清单完成日期**: _______________
**检查人员签名**: _______________
