# Nautilus 部署指南

## 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [Docker 部署](#docker-部署)
- [手动部署](#手动部署)
- [环境变量配置](#环境变量配置)
- [健康检查](#健康检查)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)

---

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/nautilus-core.git
cd nautilus-core/phase3

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必需的配置

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f backend frontend
```

访问：
- 前端：http://localhost
- 后端 API：http://localhost:8001
- Grafana：http://localhost:3000 (admin/admin)
- Prometheus：http://localhost:9090

---

## 环境要求

### 最低配置
- CPU: 2核
- 内存: 4GB
- 磁盘: 20GB
- 操作系统: Linux/macOS/Windows (with WSL2)

### 推荐配置
- CPU: 4核+
- 内存: 8GB+
- 磁盘: 50GB+ SSD
- 操作系统: Ubuntu 22.04 LTS

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+

---

## Docker 部署

### 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | React 前端 (Nginx) |
| backend | 8001 | FastAPI 后端 |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |
| chromadb | 8000 | 向量数据库 |
| prometheus | 9090 | 指标收集 |
| grafana | 3000 | 监控面板 |
| loki | 3100 | 日志聚合 |
| alertmanager | 9093 | 告警管理 |

### 部署步骤

#### 1. 准备环境变量

```bash
cp .env.example .env
nano .env
```

必需配置：
```bash
DATABASE_URL=postgresql://nautilus:your_password@postgres:5432/nautilus
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
REDIS_URL=redis://redis:6379/0
ETHEREUM_RPC_URL=https://mainnet.base.org
```

#### 2. 启动服务

```bash
docker-compose up -d
docker-compose logs -f
docker-compose ps
```

#### 3. 初始化数据库

```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/seed_data.py
```

#### 4. 验证部署

```bash
curl http://localhost:8001/health
curl http://localhost/
curl http://localhost:8001/api/stats
```

---

## 环境变量配置

### 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| DATABASE_URL | PostgreSQL 连接字符串 | postgresql://user:pass@host:5432/db |
| JWT_SECRET | JWT 签名密钥（≥32字符） | your-super-secret-key-min-32-chars |
| REDIS_URL | Redis 连接字符串 | redis://localhost:6379/0 |
| ETHEREUM_RPC_URL | 以太坊 RPC 端点 | https://mainnet.base.org |

### 生成安全密钥

```bash
openssl rand -base64 32
```

---

## 健康检查

```bash
# 后端健康检查
curl http://localhost:8001/health

# 前端健康检查
curl http://localhost/health

# 数据库连接测试
docker-compose exec postgres psql -U nautilus -d nautilus -c "SELECT 1;"

# Redis 连接测试
docker-compose exec redis redis-cli PING
```

---

## 监控和日志

### Grafana 监控

访问 http://localhost:3000 (admin/admin)

### Prometheus 指标

访问 http://localhost:9090

### 日志查看

```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs --tail=100 backend
```

---

## 故障排除

### 后端无法启动

```bash
docker-compose logs backend
docker-compose exec postgres pg_isready
docker-compose exec backend env | grep DATABASE_URL
```

### 前端无法访问后端

```bash
curl http://localhost:8001/health
# 更新 CORS_ORIGINS 环境变量
docker-compose restart backend
```

### 数据库迁移失败

```bash
docker-compose exec backend alembic current
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

---

## 安全建议

```bash
# 使用强密码
JWT_SECRET=$(openssl rand -base64 32)

# 限制 CORS
CORS_ORIGINS=https://yourdomain.com

# 定期备份
docker-compose exec postgres pg_dump -U nautilus nautilus > backup.sql
```

---

**最后更新**: 2026-03-14
**版本**: 3.0.0
