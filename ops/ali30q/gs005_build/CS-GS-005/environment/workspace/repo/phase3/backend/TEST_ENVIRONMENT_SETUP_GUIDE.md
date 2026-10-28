# Nautilus Phase 3 Backend - 测试环境配置指南

**版本**: 1.0.0
**生成日期**: 2026-02-26
**目标环境**: 测试环境 (Test Environment)
**区块链网络**: Sepolia 测试网

---

## 📖 目录

1. [概述](#概述)
2. [系统要求](#系统要求)
3. [环境准备](#环境准备)
4. [数据库配置](#数据库配置)
5. [Redis配置](#redis配置)
6. [区块链配置](#区块链配置)
7. [环境变量详解](#环境变量详解)
8. [私钥管理](#私钥管理)
9. [安全配置](#安全配置)
10. [监控和日志](#监控和日志)
11. [常见问题](#常见问题)

---

## 概述

本指南详细说明如何配置 Nautilus Phase 3 Backend 的测试环境。测试环境用于：

- 功能测试和集成测试
- 性能测试
- 用户验收测试 (UAT)
- 开发团队协作测试

测试环境使用 Sepolia 测试网，不涉及真实资金。

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核心 | 4 核心 |
| 内存 | 4GB | 8GB |
| 磁盘 | 20GB | 50GB SSD |
| 网络 | 10Mbps | 100Mbps |

### 软件要求

| 软件 | 版本要求 |
|------|---------|
| 操作系统 | Ubuntu 20.04+ / CentOS 8+ / Debian 11+ |
| Python | 3.9+ |
| PostgreSQL | 13+ |
| Redis | 6+ |
| Docker | 20.10+ (可选) |
| Docker Compose | 1.29+ (可选) |
| Git | 2.30+ |

---

## 环境准备

### 1. 安装系统依赖

#### Ubuntu/Debian

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y build-essential curl wget git vim

# 安装 Python 3.9+
sudo apt install -y python3.9 python3.9-venv python3.9-dev python3-pip

# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 安装 Redis
sudo apt install -y redis-server

# 安装 Node.js (用于智能合约部署)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### CentOS/RHEL

```bash
# 更新系统
sudo yum update -y

# 安装基础工具
sudo yum install -y gcc gcc-c++ make curl wget git vim

# 安装 Python 3.9+
sudo yum install -y python39 python39-devel python39-pip

# 安装 PostgreSQL
sudo yum install -y postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 安装 Redis
sudo yum install -y redis
sudo systemctl start redis
sudo systemctl enable redis
```

### 2. 安装 Docker (可选)

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 克隆代码仓库

```bash
# 克隆仓库
git clone <repository-url> nautilus-backend
cd nautilus-backend/phase3/backend

# 切换到测试分支
git checkout test

# 创建 Python 虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 数据库配置

### 1. PostgreSQL 安装和配置

#### 创建数据库和用户

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 PostgreSQL 中执行
CREATE DATABASE nautilus_test;
CREATE USER nautilus_test WITH PASSWORD 'en-t8JCHMse56q9sTVlsXzjm3v6ZuuIF';
GRANT ALL PRIVILEGES ON DATABASE nautilus_test TO nautilus_test;

# 授予 schema 权限
\c nautilus_test
GRANT ALL ON SCHEMA public TO nautilus_test;

# 退出
\q
```

#### 配置 PostgreSQL 访问

编辑 `/etc/postgresql/13/main/pg_hba.conf`:

```conf
# 允许本地连接
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5

# 如果需要远程访问（仅测试环境）
host    nautilus_test   nautilus_test   0.0.0.0/0               md5
```

编辑 `/etc/postgresql/13/main/postgresql.conf`:

```conf
# 监听地址
listen_addresses = 'localhost'  # 或 '*' 如果需要远程访问

# 连接数
max_connections = 100

# 内存配置
shared_buffers = 256MB
effective_cache_size = 1GB
```

重启 PostgreSQL:

```bash
sudo systemctl restart postgresql
```

#### 测试数据库连接

```bash
# 使用 psql 测试
psql -U nautilus_test -d nautilus_test -h localhost -W

# 使用 Python 测试
python -c "
import psycopg2
conn = psycopg2.connect(
    'postgresql://nautilus_test:en-t8JCHMse56q9sTVlsXzjm3v6ZuuIF@localhost:5432/nautilus_test'
)
print('Database connection successful!')
conn.close()
"
```

### 2. 数据库迁移

```bash
# 运行迁移脚本
python manage.py migrate

# 或使用 Alembic
alembic upgrade head

# 验证表创建
psql -U nautilus_test -d nautilus_test -c "\dt"
```

---

## Redis配置

### 1. Redis 安装和配置

编辑 `/etc/redis/redis.conf`:

```conf
# 绑定地址
bind 127.0.0.1

# 端口
port 6379

# 密码
requirepass A1y2lVYj3-3c3__ZZpH5cmOdUv4MQi8-

# 持久化
save 900 1
save 300 10
save 60 10000

# 最大内存
maxmemory 512mb
maxmemory-policy allkeys-lru

# 日志
loglevel notice
logfile /var/log/redis/redis-server.log
```

重启 Redis:

```bash
sudo systemctl restart redis
```

### 2. 测试 Redis 连接

```bash
# 使用 redis-cli 测试
redis-cli -a A1y2lVYj3-3c3__ZZpH5cmOdUv4MQi8-
> PING
PONG
> SET test "Hello"
OK
> GET test
"Hello"
> exit

# 使用 Python 测试
python -c "
import redis
r = redis.Redis(
    host='localhost',
    port=6379,
    password='A1y2lVYj3-3c3__ZZpH5cmOdUv4MQi8-',
    db=1
)
r.set('test', 'Hello')
print(r.get('test'))
"
```

---

## 区块链配置

### 1. 获取 Infura/Alchemy API Key

#### Infura

1. 访问 https://infura.io/
2. 注册账户
3. 创建新项目
4. 选择 Ethereum 网络
5. 复制 Project ID
6. Sepolia RPC URL: `https://sepolia.infura.io/v3/YOUR_PROJECT_ID`

#### Alchemy (备选)

1. 访问 https://www.alchemy.com/
2. 注册账户
3. 创建新应用
4. 选择 Sepolia 网络
5. 复制 API Key
6. Sepolia RPC URL: `https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY`

### 2. 获取测试 ETH

从 Sepolia 水龙头获取测试 ETH:

- https://sepoliafaucet.com/
- https://faucet.sepolia.dev/
- https://sepolia-faucet.pk910.de/

### 3. 部署智能合约

```bash
# 进入合约目录
cd contracts

# 安装依赖
npm install

# 配置 Hardhat
# 编辑 hardhat.config.js
module.exports = {
  networks: {
    sepolia: {
      url: "https://sepolia.infura.io/v3/YOUR_PROJECT_ID",
      accounts: ["YOUR_PRIVATE_KEY"]
    }
  }
};

# 编译合约
npx hardhat compile

# 部署到 Sepolia
npx hardhat deploy --network sepolia

# 记录合约地址
# 输出示例:
# IdentityContract deployed to: 0x1234...
# TaskContract deployed to: 0x5678...
# RewardContract deployed to: 0x9abc...

# 验证合约
npx hardhat verify --network sepolia <contract-address>
```

### 4. 配置合约地址

将部署的合约地址填入 `.env.test`:

```bash
IDENTITY_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
TASK_CONTRACT_ADDRESS=0x2345678901234567890123456789012345678901
TASK_MARKET_ADDRESS=0x3456789012345678901234567890123456789012
REWARD_CONTRACT_ADDRESS=0x4567890123456789012345678901234567890123
REWARD_POOL_ADDRESS=0x5678901234567890123456789012345678901234
AGENT_REGISTRY_ADDRESS=0x6789012345678901234567890123456789012345
```

---

## 环境变量详解

### 核心配置

#### ENVIRONMENT
- **说明**: 环境标识
- **值**: `test`
- **必需**: 是

#### DEBUG
- **说明**: 调试模式
- **值**: `false` (测试环境建议关闭)
- **必需**: 是

#### LOG_LEVEL
- **说明**: 日志级别
- **值**: `debug` | `info` | `warning` | `error`
- **推荐**: `info`
- **必需**: 是

### 服务器配置

#### HOST
- **说明**: 监听地址
- **值**: `0.0.0.0` (监听所有接口) 或 `127.0.0.1` (仅本地)
- **必需**: 是

#### PORT
- **说明**: API 服务端口
- **值**: `8000`
- **必需**: 是

#### NEXUS_PORT
- **说明**: Nexus 协议端口
- **值**: `8001`
- **必需**: 是

#### MAX_AGENTS
- **说明**: 最大 Agent 数量
- **值**: `50` (测试环境)
- **必需**: 是

#### MAX_QUEUE_SIZE
- **说明**: 最大队列大小
- **值**: `500` (测试环境)
- **必需**: 是

### 数据库配置

#### DATABASE_URL
- **说明**: PostgreSQL 连接字符串
- **格式**: `postgresql://用户名:密码@主机:端口/数据库名`
- **示例**: `postgresql://nautilus_test:password@localhost:5432/nautilus_test`
- **必需**: 是

#### DB_POOL_SIZE
- **说明**: 连接池大小
- **值**: `10` (测试环境)
- **必需**: 否

#### DB_MAX_OVERFLOW
- **说明**: 最大溢出连接数
- **值**: `20`
- **必需**: 否

### Redis 配置

#### REDIS_URL
- **说明**: Redis 连接字符串
- **格式**: `redis://:密码@主机:端口/数据库`
- **示例**: `redis://:password@localhost:6379/1`
- **必需**: 是

#### REDIS_DB
- **说明**: Redis 数据库编号
- **值**: `1` (测试环境使用 DB 1，区分生产环境)
- **必需**: 是

### 安全配置

#### JWT_SECRET_KEY
- **说明**: JWT 签名密钥
- **生成**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **必需**: 是
- **注意**: 必须使用强随机密钥

#### CSRF_SECRET_KEY
- **说明**: CSRF 保护密钥
- **生成**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **必需**: 是
- **注意**: 必须与 JWT_SECRET_KEY 不同

#### JWT_EXPIRATION_MINUTES
- **说明**: JWT Token 过期时间（分钟）
- **值**: `30`
- **必需**: 否

### CORS 配置

#### CORS_ORIGINS
- **说明**: 允许的跨域源
- **格式**: 逗号分隔的 URL 列表
- **示例**: `http://localhost:3000,http://test.nautilus.local`
- **必需**: 是
- **注意**: 不要使用通配符 `*`

### 区块链配置

#### BLOCKCHAIN_NETWORK
- **说明**: 区块链网络
- **值**: `sepolia` (测试环境)
- **必需**: 是

#### BLOCKCHAIN_RPC_URL
- **说明**: RPC 节点 URL
- **示例**: `https://sepolia.infura.io/v3/YOUR_PROJECT_ID`
- **必需**: 是

#### INFURA_PROJECT_ID
- **说明**: Infura 项目 ID
- **获取**: https://infura.io/
- **必需**: 是

#### 合约地址配置

所有合约地址必须填入部署后的实际地址:

- `IDENTITY_CONTRACT_ADDRESS`
- `TASK_CONTRACT_ADDRESS`
- `TASK_MARKET_ADDRESS`
- `REWARD_CONTRACT_ADDRESS`
- `REWARD_POOL_ADDRESS`
- `AGENT_REGISTRY_ADDRESS`

### 速率限制配置

#### RATE_LIMIT_ENABLED
- **说明**: 是否启用速率限制
- **值**: `true`
- **必需**: 是

#### RATE_LIMIT_LOGIN
- **说明**: 登录接口速率限制
- **值**: `10/minute` (测试环境宽松)
- **必需**: 否

#### RATE_LIMIT_API
- **说明**: 通用 API 速率限制
- **值**: `200/minute`
- **必需**: 否

---

## 私钥管理

### 方式 1: 环境变量（简单但不推荐）

```bash
# 在 .env.test 中
BLOCKCHAIN_PRIVATE_KEY=0x1234567890abcdef...
```

**优点**: 简单直接
**缺点**: 安全性低，容易泄露

### 方式 2: 加密文件存储（推荐）

#### 步骤 1: 创建加密脚本

创建 `scripts/generate_encrypted_key.py`:

```python
import json
import sys
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_private_key(private_key: str, password: str, output_file: str):
    # 生成盐
    salt = os.urandom(16)

    # 从密码生成密钥
    key = generate_key_from_password(password, salt)

    # 加密私钥
    f = Fernet(key)
    encrypted_key = f.encrypt(private_key.encode())

    # 保存到文件
    data = {
        'salt': base64.b64encode(salt).decode(),
        'encrypted_key': encrypted_key.decode()
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Encrypted key saved to: {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_encrypted_key.py <output_file>")
        sys.exit(1)

    output_file = sys.argv[1]
    private_key = getpass.getpass("Enter private key: ")
    password = getpass.getpass("Enter encryption password: ")

    encrypt_private_key(private_key, password, output_file)
```

#### 步骤 2: 生成加密密钥文件

```bash
# 创建密钥目录
mkdir -p keys
chmod 700 keys

# 生成加密密钥文件
python scripts/generate_encrypted_key.py keys/test_encrypted_key.json

# 输入私钥和加密密码
# Enter private key: 0x1234...
# Enter encryption password: ********

# 设置文件权限
chmod 600 keys/test_encrypted_key.json
```

#### 步骤 3: 配置环境变量

```bash
# 在 .env.test 中
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=/c/Users/chunx/Projects/nautilus-core/phase3/backend/keys/test_encrypted_key.json
KEY_ENCRYPTION_PASSWORD=your-encryption-password
```

### 方式 3: AWS KMS（云环境推荐）

```bash
# 在 .env.test 中
KEY_SOURCE=aws_kms
AWS_KMS_KEY_ID=arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
AWS_REGION=us-east-1
BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED=base64-encoded-encrypted-key
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
```

---

## 安全配置

### 1. 文件权限

```bash
# .env.test 文件权限
chmod 600 .env.test

# 密钥目录权限
chmod 700 keys/
chmod 600 keys/*

# 日志目录权限
sudo mkdir -p /var/log/nautilus
sudo chown $USER:$USER /var/log/nautilus
chmod 755 /var/log/nautilus
```

### 2. 防火墙配置

```bash
# 使用 ufw (Ubuntu)
sudo ufw allow 8000/tcp  # API 端口
sudo ufw allow 8001/tcp  # Nexus 端口
sudo ufw enable

# 使用 firewalld (CentOS)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --reload
```

### 3. SSL/TLS 配置（可选）

测试环境可以使用自签名证书:

```bash
# 生成自签名证书
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# 配置环境变量
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

---

## 监控和日志

### 1. 日志配置

创建日志目录:

```bash
sudo mkdir -p /var/log/nautilus
sudo chown $USER:$USER /var/log/nautilus
```

配置日志轮转 `/etc/logrotate.d/nautilus`:

```conf
/var/log/nautilus/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 nautilus nautilus
}
```

### 2. Prometheus 监控

访问 Prometheus 指标:

```bash
curl http://localhost:9090/metrics
```

### 3. 健康检查

```bash
# 健康检查端点
curl http://localhost:8000/health

# 详细状态
curl http://localhost:8000/api/v1/status
```

---

## 常见问题

### Q1: 数据库连接失败

**问题**: `psycopg2.OperationalError: could not connect to server`

**解决方案**:
```bash
# 检查 PostgreSQL 服务
sudo systemctl status postgresql

# 检查连接配置
psql -U nautilus_test -d nautilus_test -h localhost

# 检查 pg_hba.conf 配置
sudo vim /etc/postgresql/13/main/pg_hba.conf
```

### Q2: Redis 连接失败

**问题**: `redis.exceptions.ConnectionError`

**解决方案**:
```bash
# 检查 Redis 服务
sudo systemctl status redis

# 测试连接
redis-cli -a <password> ping

# 检查配置
sudo vim /etc/redis/redis.conf
```

### Q3: 区块链 RPC 连接超时

**问题**: `requests.exceptions.Timeout`

**解决方案**:
```bash
# 测试 RPC 连接
curl -X POST https://sepolia.infura.io/v3/<project-id> \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# 检查 Infura 配额
# 访问 Infura 控制台查看请求统计
```

### Q4: 端口被占用

**问题**: `OSError: [Errno 98] Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
sudo lsof -i :8000

# 停止进程
sudo kill -9 <PID>

# 或更改端口
PORT=8002 python main.py
```

### Q5: 权限不足

**问题**: `PermissionError: [Errno 13] Permission denied`

**解决方案**:
```bash
# 检查文件权限
ls -la .env.test

# 修复权限
chmod 600 .env.test
chown $USER:$USER .env.test

# 检查目录权限
sudo chown -R $USER:$USER /var/log/nautilus
```

### Q6: 内存不足

**问题**: 应用崩溃或性能下降

**解决方案**:
```bash
# 检查内存使用
free -h

# 减少 Worker 数量
WORKERS=1 python main.py

# 减少数据库连接池
DB_POOL_SIZE=5
```

### Q7: 智能合约调用失败

**问题**: `Web3.exceptions.ContractLogicError`

**解决方案**:
```bash
# 检查合约地址
echo $TASK_CONTRACT_ADDRESS

# 检查账户余额
curl -X POST https://sepolia.infura.io/v3/<project-id> \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["<address>","latest"],"id":1}'

# 从水龙头获取测试 ETH
# https://sepoliafaucet.com/
```

---

## 附录

### A. 完整的 .env.test 模板

参见项目根目录的 `.env.test` 文件。

### B. 部署脚本

参见 `deploy.sh` 和 `docker-compose.test.yml`。

### C. 测试脚本

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 运行性能测试
locust -f tests/performance/locustfile.py
```

### D. 有用的命令

```bash
# 查看应用日志
tail -f /var/log/nautilus/test_app.log

# 查看数据库连接
psql -U nautilus_test -d nautilus_test -c "SELECT * FROM pg_stat_activity;"

# 查看 Redis 信息
redis-cli -a <password> INFO

# 查看进程状态
ps aux | grep python

# 查看端口监听
sudo netstat -tulpn | grep -E '8000|8001'
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-26
**维护者**: Nautilus DevOps Team
