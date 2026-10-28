# 生产部署配置使用指南

## 概述

本目录包含了 Nautilus Phase 3 Backend 生产环境部署所需的所有脚本、配置模板和文档。

## 文件结构

```
backend/
├── scripts/
│   └── deploy/
│       ├── deploy_production.sh      # 生产部署脚本
│       ├── check_deployment.sh       # 部署检查脚本
│       └── validate_config.sh        # 配置验证脚本
├── .env.production.template          # 环境变量模板
├── docker-compose.prod.yml           # 生产环境Docker配置
├── SERVER_REQUIREMENTS.md            # 服务器配置清单
├── PRODUCTION_DEPLOYMENT_STEPS.md    # 详细部署步骤
├── PRODUCTION_DEPLOYMENT_PLAN.md     # 部署计划
└── DEPLOYMENT_CONFIG_SUMMARY.md      # 配置总结
```

## 快速开始

### 1. 准备配置文件

```bash
# 复制环境变量模板
cp .env.production.template .env.production

# 编辑配置文件
vim .env.production

# 生成密钥
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('CSRF_SECRET_KEY=' + secrets.token_urlsafe(64))"
```

### 2. 验证配置

```bash
# 验证配置文件
./scripts/deploy/validate_config.sh

# 如果有错误，根据提示修改配置文件
```

### 3. 执行部署

```bash
# 模拟运行（推荐先执行）
./scripts/deploy/deploy_production.sh --dry-run --version 1.0.0

# 实际部署
./scripts/deploy/deploy_production.sh --version 1.0.0
```

### 4. 验证部署

```bash
# 运行检查脚本
./scripts/deploy/check_deployment.sh --verbose

# 检查特定主机
./scripts/deploy/check_deployment.sh --host production.example.com
```

## 脚本说明

### deploy_production.sh

**功能**: 自动化生产部署

**选项**:
- `--version VERSION`: 指定部署版本
- `--skip-backup`: 跳过备份步骤
- `--skip-tests`: 跳过部署后测试
- `--rollback`: 回滚到上一个版本
- `--dry-run`: 模拟运行

**示例**:
```bash
# 部署指定版本
./scripts/deploy/deploy_production.sh --version v1.2.3

# 回滚
./scripts/deploy/deploy_production.sh --rollback
```

### check_deployment.sh

**功能**: 部署后全面检查

**选项**:
- `--host HOST`: 指定主机地址
- `--port PORT`: 指定端口
- `--timeout SECONDS`: 超时时间
- `--verbose`: 详细输出
- `--json`: JSON格式输出

**示例**:
```bash
# 基本检查
./scripts/deploy/check_deployment.sh

# 详细检查
./scripts/deploy/check_deployment.sh --verbose

# JSON输出（用于监控系统）
./scripts/deploy/check_deployment.sh --json
```

### validate_config.sh

**功能**: 验证配置文件

**示例**:
```bash
# 验证默认配置
./scripts/deploy/validate_config.sh

# 验证指定配置
./scripts/deploy/validate_config.sh /path/to/.env.production
```

## 配置文件说明

### .env.production.template

包含所有必需的环境变量配置项，分为以下几类：

1. **环境配置**: ENVIRONMENT, DEBUG, LOG_LEVEL
2. **服务器配置**: HOST, PORT, WORKERS
3. **数据库配置**: DATABASE_URL, 连接池
4. **Redis配置**: REDIS_URL, 连接参数
5. **安全配置**: JWT密钥, CSRF密钥
6. **CORS配置**: 允许的域名
7. **区块链配置**: RPC URL, 合约地址
8. **监控配置**: Prometheus, Sentry
9. **备份配置**: 本地和S3备份

### 必须修改的配置项

在部署前，以下配置项**必须**修改：

```bash
# 密钥（生成64字符以上的随机字符串）
JWT_SECRET_KEY=CHANGE_THIS
CSRF_SECRET_KEY=CHANGE_THIS

# 数据库
DATABASE_URL=postgresql://user:password@host:5432/db

# Redis
REDIS_PASSWORD=CHANGE_THIS

# CORS（修改为实际域名）
CORS_ORIGINS=https://yourdomain.com

# 区块链
BLOCKCHAIN_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
INFURA_PROJECT_ID=YOUR_PROJECT_ID

# 智能合约地址
IDENTITY_CONTRACT_ADDRESS=0x...
TASK_CONTRACT_ADDRESS=0x...
```

## 部署流程

### 完整部署流程

1. **准备阶段**
   - 阅读 `SERVER_REQUIREMENTS.md`
   - 准备服务器
   - 安装必需软件

2. **配置阶段**
   - 复制配置模板
   - 修改配置文件
   - 验证配置

3. **部署阶段**
   - 执行部署脚本
   - 监控部署过程
   - 处理错误

4. **验证阶段**
   - 运行检查脚本
   - 手动验证关键功能
   - 性能测试

5. **监控阶段**
   - 持续监控系统状态
   - 查看日志
   - 响应告警

### 零停机部署

部署脚本支持零停机部署：

1. 启动新版本容器
2. 等待健康检查通过
3. 切换流量到新版本
4. 停止旧版本容器

### 回滚流程

如果部署出现问题，可以快速回滚：

```bash
# 自动回滚
./scripts/deploy/deploy_production.sh --rollback

# 手动回滚
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.old.yml up -d
```

## 监控和维护

### 日常检查

```bash
# 每日运行检查脚本
./scripts/deploy/check_deployment.sh

# 查看日志
docker logs --tail 100 nexus-server-prod

# 检查资源使用
docker stats nexus-server-prod
```

### 定期维护

```bash
# 每周清理Docker资源
docker system prune -a --volumes -f

# 每月检查备份
ls -lh /var/backups/nautilus/database/

# 更新系统
sudo apt update && sudo apt upgrade -y
```

### 日志位置

- **应用日志**: `/var/log/nautilus/app.log`
- **审计日志**: `/var/log/nautilus/audit.log`
- **部署日志**: `/var/log/nautilus/deploy_*.log`
- **Docker日志**: `docker logs nexus-server-prod`

## 故障排查

### 常见问题

#### 1. 部署脚本执行失败

```bash
# 检查权限
ls -l scripts/deploy/*.sh

# 添加执行权限
chmod +x scripts/deploy/*.sh

# 检查依赖
which docker docker-compose curl jq
```

#### 2. 配置验证失败

```bash
# 查看详细错误信息
./scripts/deploy/validate_config.sh

# 根据错误提示修改配置
vim .env.production
```

#### 3. 服务无法启动

```bash
# 查看容器日志
docker logs nexus-server-prod

# 检查配置文件
cat .env.production

# 检查端口占用
netstat -tuln | grep 8001
```

#### 4. 健康检查失败

```bash
# 手动测试健康检查端点
curl http://localhost:8001/health

# 检查数据库连接
psql -h localhost -U nautilus_user -d nautilus_production

# 检查Redis连接
redis-cli -a your_password ping
```

### 获取帮助

如果遇到问题：

1. 查看 `PRODUCTION_DEPLOYMENT_STEPS.md` 第7章（故障排查）
2. 检查日志文件
3. 联系技术支持: support@yourdomain.com

## 安全注意事项

### 配置文件安全

```bash
# 设置正确的文件权限
chmod 600 .env.production

# 不要提交到版本控制
echo ".env.production" >> .gitignore

# 使用密钥管理服务（推荐）
# AWS KMS, Azure Key Vault, HashiCorp Vault
```

### 密钥管理

```bash
# 生成强密钥
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 定期轮换密钥（建议每90天）
# 配置 KEY_ROTATION_ENABLED=true
```

### 访问控制

```bash
# 限制SSH访问
sudo ufw allow from 192.168.1.0/24 to any port 22

# 使用密钥认证
ssh-keygen -t ed25519
ssh-copy-id user@server

# 禁用密码登录
sudo vim /etc/ssh/sshd_config
# PasswordAuthentication no
```

## 性能优化

### 数据库优化

```bash
# 调整PostgreSQL配置
sudo vim /etc/postgresql/16/main/postgresql.conf

# 关键参数（16GB内存服务器）
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 20MB
```

### 应用优化

```bash
# 调整Worker数量（等于CPU核心数）
WORKERS=4

# 调整连接池
DB_POOL_SIZE=20
REDIS_MAX_CONNECTIONS=50
```

### 缓存优化

```bash
# 启用缓存
CACHE_ENABLED=true
CACHE_TTL=300

# 调整Redis内存
maxmemory 8gb
maxmemory-policy allkeys-lru
```

## 备份和恢复

### 自动备份

备份脚本会自动执行：
- 数据库备份: 每天凌晨2点
- 保留期: 30天
- 位置: `/var/backups/nautilus/`

### 手动备份

```bash
# 备份数据库
pg_dump -h localhost -U nautilus_user nautilus_production | \
    gzip > backup_$(date +%Y%m%d).sql.gz

# 备份配置
cp .env.production .env.production.backup
```

### 恢复数据

```bash
# 恢复数据库
gunzip -c backup_20260227.sql.gz | \
    psql -h localhost -U nautilus_user nautilus_production

# 恢复配置
cp .env.production.backup .env.production
```

## 更新和升级

### 应用更新

```bash
# 1. 拉取新代码
git pull origin main

# 2. 部署新版本
./scripts/deploy/deploy_production.sh --version v1.1.0

# 3. 验证部署
./scripts/deploy/check_deployment.sh
```

### 系统更新

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 更新Docker
sudo apt install docker-ce docker-ce-cli containerd.io

# 重启服务
sudo systemctl restart docker
```

## 监控集成

### Prometheus

```bash
# 访问指标端点
curl http://localhost:9090/metrics

# 配置Prometheus
# 参考 MONITORING_GUIDE.md
```

### Grafana

```bash
# 访问Grafana
http://monitoring.yourdomain.com:3000

# 默认凭据（首次登录后修改）
# 用户名: admin
# 密码: admin
```

## 文档索引

- **[SERVER_REQUIREMENTS.md](SERVER_REQUIREMENTS.md)**: 服务器硬件、软件、网络要求
- **[PRODUCTION_DEPLOYMENT_STEPS.md](PRODUCTION_DEPLOYMENT_STEPS.md)**: 详细部署步骤和故障排查
- **[PRODUCTION_DEPLOYMENT_PLAN.md](PRODUCTION_DEPLOYMENT_PLAN.md)**: 完整部署计划和时间表
- **[DEPLOYMENT_CONFIG_SUMMARY.md](DEPLOYMENT_CONFIG_SUMMARY.md)**: 配置总结和快速参考
- **[.env.production.template](.env.production.template)**: 环境变量配置模板

## 支持

- **文档**: 查看上述文档获取详细信息
- **邮件**: support@yourdomain.com
- **紧急**: +86-xxx-xxxx-xxxx

---

**祝部署顺利！**
