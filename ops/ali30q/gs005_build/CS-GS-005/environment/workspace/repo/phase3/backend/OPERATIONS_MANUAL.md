# Nautilus Phase 3 Backend - 运维完整手册

**版本**: 3.0.0
**日期**: 2026-02-26
**维护团队**: Nautilus 运维团队

---

## 📖 目录

1. [系统架构概述](#系统架构概述)
2. [日常运维流程](#日常运维流程)
3. [变更管理流程](#变更管理流程)
4. [应急响应流程](#应急响应流程)
5. [系统维护](#系统维护)
6. [安全管理](#安全管理)
7. [容量规划](#容量规划)
8. [文档管理](#文档管理)

---

## 系统架构概述

### 1.1 系统组件

Nautilus Phase 3 是一个基于区块链的多智能体任务协作平台，包含以下核心组件：

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │  Nginx  │ (反向代理/负载均衡)
                    │  :443   │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │ FastAPI │     │ FastAPI │     │ FastAPI │
   │  :8000  │     │  :8001  │     │  :8002  │
   └────┬────┘     └────┬────┘     └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │PostgreSQL│    │  Redis  │     │Blockchain│
   │  :5432  │     │  :6379  │     │ (Sepolia)│
   └─────────┘     └─────────┘     └──────────┘
        │                │
   ┌────▼────┐     ┌────▼────┐
   │Prometheus│    │ Grafana │
   │  :9090  │     │  :3000  │
   └─────────┘     └─────────┘
```

### 1.2 技术栈

**应用层**:
- FastAPI 0.104.1 - Web 框架
- Python 3.13+ - 编程语言
- Uvicorn 0.24.0 - ASGI 服务器
- Socket.IO 5.10.0 - WebSocket 通信

**数据层**:
- PostgreSQL 15 - 主数据库
- Redis 7 - 缓存和会话
- SQLAlchemy 2.0+ - ORM

**区块链层**:
- Web3.py 6.0+ - 以太坊交互
- Sepolia 测试网 - 区块链网络
- Infura - RPC 节点服务

**监控层**:
- Prometheus - 指标收集
- Grafana - 数据可视化
- 自定义日志系统

### 1.3 服务端口

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| Nginx | 80 | HTTP | HTTP 访问（重定向到 HTTPS） |
| Nginx | 443 | HTTPS | HTTPS 访问 |
| FastAPI | 8000 | HTTP | 主 API 服务 |
| Nexus Server | 8001 | HTTP/WS | Agent 通信服务 |
| PostgreSQL | 5432 | TCP | 数据库服务 |
| Redis | 6379 | TCP | 缓存服务 |
| Prometheus | 9090 | HTTP | 监控指标 |
| Grafana | 3000 | HTTP | 监控面板 |

### 1.4 关键文件路径

```bash
# 应用目录
/opt/nautilus/backend/              # 应用根目录
/opt/nautilus/backend/main.py       # 主应用入口
/opt/nautilus/backend/nexus_server.py  # Nexus 服务器

# 配置文件
/opt/nautilus/backend/.env          # 环境变量配置
/opt/nautilus/backend/.env.production  # 生产环境配置
/etc/nginx/sites-available/nautilus    # Nginx 配置

# 日志文件
/var/log/nautilus/app.log           # 应用日志
/var/log/nautilus/error.log         # 错误日志
/var/log/nautilus/access.log        # 访问日志
/var/log/nginx/nautilus.access.log  # Nginx 访问日志
/var/log/nginx/nautilus.error.log   # Nginx 错误日志

# 数据目录
/var/lib/postgresql/15/main/        # PostgreSQL 数据
/var/lib/redis/                     # Redis 数据

# 密钥管理
/opt/nautilus/backend/keys/         # 加密密钥存储
/opt/nautilus/backend/keys/master.key  # 主密钥
```

---

## 日常运维流程

### 2.1 每日检查清单

#### 2.1.1 服务状态检查

```bash
#!/bin/bash
# 每日服务状态检查脚本

echo "=== Nautilus 每日健康检查 ==="
echo "检查时间: $(date)"
echo ""

# 1. 检查应用服务
echo "1. 检查应用服务状态..."
systemctl status nautilus-backend
systemctl status nautilus-nexus

# 2. 检查数据库
echo "2. 检查数据库状态..."
systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"
sudo -u postgres psql -d nautilus_prod -c "SELECT COUNT(*) FROM users;"

# 3. 检查 Redis
echo "3. 检查 Redis 状态..."
systemctl status redis
redis-cli ping

# 4. 检查 Nginx
echo "4. 检查 Nginx 状态..."
systemctl status nginx
nginx -t

# 5. 检查磁盘空间
echo "5. 检查磁盘空间..."
df -h | grep -E '(Filesystem|/dev/)'

# 6. 检查内存使用
echo "6. 检查内存使用..."
free -h

# 7. 检查 API 健康
echo "7. 检查 API 健康..."
curl -s http://localhost:8000/health | jq .

# 8. 检查区块链连接
echo "8. 检查区块链连接..."
curl -s http://localhost:8000/api/blockchain/health | jq .

# 9. 检查最近错误日志
echo "9. 检查最近错误（最近 1 小时）..."
journalctl -u nautilus-backend --since "1 hour ago" --priority=err

echo ""
echo "=== 检查完成 ==="
```

#### 2.1.2 性能指标检查

```bash
#!/bin/bash
# 性能指标检查脚本

echo "=== 性能指标检查 ==="

# 1. API 响应时间
echo "1. API 响应时间测试..."
time curl -s http://localhost:8000/health > /dev/null

# 2. 数据库连接数
echo "2. 数据库连接数..."
sudo -u postgres psql -d nautilus_prod -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Redis 内存使用
echo "3. Redis 内存使用..."
redis-cli info memory | grep used_memory_human

# 4. 活跃任务数
echo "4. 活跃任务数..."
curl -s http://localhost:8000/api/tasks/stats | jq .

# 5. 在线 Agent 数
echo "5. 在线 Agent 数..."
curl -s http://localhost:8000/api/agents/stats | jq .

# 6. 系统负载
echo "6. 系统负载..."
uptime

# 7. CPU 使用率
echo "7. CPU 使用率..."
top -bn1 | grep "Cpu(s)"

# 8. 网络连接数
echo "8. 网络连接数..."
ss -s
```

#### 2.1.3 日志检查

```bash
#!/bin/bash
# 日志检查脚本

echo "=== 日志检查 ==="

# 1. 检查应用错误日志
echo "1. 应用错误日志（最近 24 小时）..."
tail -n 100 /var/log/nautilus/error.log | grep -i error

# 2. 检查数据库慢查询
echo "2. 数据库慢查询..."
sudo -u postgres psql -d nautilus_prod -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC
LIMIT 10;"

# 3. 检查 Nginx 错误
echo "3. Nginx 错误日志..."
tail -n 50 /var/log/nginx/nautilus.error.log

# 4. 检查区块链交易失败
echo "4. 区块链交易失败..."
grep "blockchain.*failed" /var/log/nautilus/app.log | tail -n 20

# 5. 检查认证失败
echo "5. 认证失败尝试..."
grep "authentication failed" /var/log/nautilus/app.log | tail -n 20
```

### 2.2 每周维护任务

#### 2.2.1 数据库维护

```bash
#!/bin/bash
# 每周数据库维护脚本

echo "=== 数据库每周维护 ==="

# 1. 数据库备份
echo "1. 执行数据库备份..."
/opt/nautilus/scripts/backup_database.sh

# 2. 清理过期数据
echo "2. 清理过期数据..."
sudo -u postgres psql -d nautilus_prod <<EOF
-- 清理 30 天前的日志
DELETE FROM system_logs WHERE created_at < NOW() - INTERVAL '30 days';

-- 清理已完成的旧任务（90 天前）
DELETE FROM tasks WHERE status = 'completed' AND completed_at < NOW() - INTERVAL '90 days';

-- 清理过期会话
DELETE FROM sessions WHERE expires_at < NOW();
EOF

# 3. 数据库优化
echo "3. 执行数据库优化..."
sudo -u postgres psql -d nautilus_prod <<EOF
-- 更新统计信息
ANALYZE;

-- 清理死元组
VACUUM ANALYZE;

-- 重建索引
REINDEX DATABASE nautilus_prod;
EOF

# 4. 检查数据库大小
echo "4. 检查数据库大小..."
sudo -u postgres psql -d nautilus_prod -c "
SELECT
    pg_size_pretty(pg_database_size('nautilus_prod')) as db_size,
    pg_size_pretty(pg_total_relation_size('tasks')) as tasks_size,
    pg_size_pretty(pg_total_relation_size('users')) as users_size,
    pg_size_pretty(pg_total_relation_size('agents')) as agents_size;
"
```

#### 2.2.2 日志轮转和清理

```bash
#!/bin/bash
# 日志清理脚本

echo "=== 日志清理 ==="

# 1. 压缩旧日志
echo "1. 压缩旧日志文件..."
find /var/log/nautilus/ -name "*.log" -mtime +7 -exec gzip {} \;

# 2. 删除超过 30 天的压缩日志
echo "2. 删除旧压缩日志..."
find /var/log/nautilus/ -name "*.log.gz" -mtime +30 -delete

# 3. 检查日志目录大小
echo "3. 日志目录大小..."
du -sh /var/log/nautilus/

# 4. 轮转 Nginx 日志
echo "4. 轮转 Nginx 日志..."
nginx -s reopen
```

### 2.3 每月维护任务

#### 2.3.1 系统更新

```bash
#!/bin/bash
# 系统更新脚本

echo "=== 系统每月更新 ==="

# 1. 备份当前系统
echo "1. 创建系统快照..."
/opt/nautilus/scripts/create_snapshot.sh

# 2. 更新系统包
echo "2. 更新系统包..."
sudo apt update
sudo apt upgrade -y

# 3. 更新 Python 依赖
echo "3. 更新 Python 依赖..."
cd /opt/nautilus/backend
source venv/bin/activate
pip list --outdated
# 谨慎更新，先在测试环境验证

# 4. 检查安全更新
echo "4. 检查安全更新..."
sudo apt list --upgradable | grep -i security

# 5. 重启服务
echo "5. 重启服务..."
sudo systemctl restart nautilus-backend
sudo systemctl restart nautilus-nexus
```

#### 2.3.2 性能报告生成

```bash
#!/bin/bash
# 生成月度性能报告

echo "=== 生成月度性能报告 ==="

REPORT_FILE="/var/log/nautilus/reports/monthly_$(date +%Y%m).txt"

{
    echo "Nautilus 月度性能报告"
    echo "报告时间: $(date)"
    echo "================================"
    echo ""

    echo "1. 系统运行时间"
    uptime
    echo ""

    echo "2. 月度 API 调用统计"
    # 从 Prometheus 获取数据
    curl -s "http://localhost:9090/api/v1/query?query=sum(increase(nautilus_http_requests_total[30d]))"
    echo ""

    echo "3. 平均响应时间"
    curl -s "http://localhost:9090/api/v1/query?query=avg(nautilus_http_request_duration_seconds)"
    echo ""

    echo "4. 错误率"
    curl -s "http://localhost:9090/api/v1/query?query=rate(nautilus_http_requests_total{status=~'5..'}[30d])"
    echo ""

    echo "5. 数据库统计"
    sudo -u postgres psql -d nautilus_prod -c "
    SELECT
        'Total Users' as metric, COUNT(*) as value FROM users
    UNION ALL
    SELECT 'Total Tasks', COUNT(*) FROM tasks
    UNION ALL
    SELECT 'Total Agents', COUNT(*) FROM agents
    UNION ALL
    SELECT 'Completed Tasks', COUNT(*) FROM tasks WHERE status = 'completed';
    "

} > "$REPORT_FILE"

echo "报告已生成: $REPORT_FILE"
```

---

## 变更管理流程

### 3.1 变更分类

| 变更类型 | 风险等级 | 审批流程 | 测试要求 | 回滚计划 |
|---------|---------|---------|---------|---------|
| 紧急修复 | 高 | 技术负责人 | 快速测试 | 必需 |
| 常规更新 | 中 | 运维负责人 | 完整测试 | 必需 |
| 配置变更 | 低 | 运维工程师 | 验证测试 | 建议 |
| 数据变更 | 高 | 技术+业务负责人 | 完整测试 | 必需 |

### 3.2 变更申请流程

#### 3.2.1 变更申请模板

```markdown
# 变更申请单

## 基本信息
- 申请人: [姓名]
- 申请时间: [YYYY-MM-DD HH:MM]
- 变更类型: [紧急修复/常规更新/配置变更/数据变更]
- 风险等级: [高/中/低]

## 变更描述
### 变更目的
[描述为什么需要这次变更]

### 变更内容
[详细描述变更的具体内容]

### 影响范围
- 影响的服务: [列出受影响的服务]
- 影响的用户: [估计受影响的用户数量]
- 预计停机时间: [分钟]

## 实施计划
### 实施步骤
1. [步骤 1]
2. [步骤 2]
3. [步骤 3]

### 实施时间
- 计划开始: [YYYY-MM-DD HH:MM]
- 计划结束: [YYYY-MM-DD HH:MM]
- 维护窗口: [是/否]

### 回滚计划
[描述如何回滚此变更]

## 测试验证
### 测试环境验证
- [ ] 功能测试通过
- [ ] 性能测试通过
- [ ] 安全测试通过

### 生产验证步骤
1. [验证步骤 1]
2. [验证步骤 2]

## 审批
- 技术负责人: [签名] [日期]
- 运维负责人: [签名] [日期]
- 业务负责人: [签名] [日期]（如需要）
```

### 3.3 变更实施流程

#### 3.3.1 标准变更流程

```bash
#!/bin/bash
# 标准变更实施脚本

set -e  # 遇到错误立即退出

CHANGE_ID="$1"
BACKUP_DIR="/opt/nautilus/backups/change_${CHANGE_ID}"

echo "=== 变更实施开始 ==="
echo "变更ID: $CHANGE_ID"
echo "时间: $(date)"

# 1. 创建备份
echo "步骤 1: 创建备份..."
mkdir -p "$BACKUP_DIR"
/opt/nautilus/scripts/backup_all.sh "$BACKUP_DIR"

# 2. 通知用户
echo "步骤 2: 发送维护通知..."
curl -X POST http://localhost:8000/api/admin/maintenance \
  -H "Content-Type: application/json" \
  -d '{"status": "starting", "message": "系统维护即将开始"}'

# 3. 启用维护模式
echo "步骤 3: 启用维护模式..."
touch /opt/nautilus/backend/MAINTENANCE_MODE

# 4. 停止服务
echo "步骤 4: 停止服务..."
systemctl stop nautilus-backend
systemctl stop nautilus-nexus

# 5. 执行变更
echo "步骤 5: 执行变更..."
# 在这里执行实际的变更操作
# 例如: 部署新代码、更新配置、数据库迁移等

# 6. 启动服务
echo "步骤 6: 启动服务..."
systemctl start nautilus-backend
systemctl start nautilus-nexus

# 7. 健康检查
echo "步骤 7: 健康检查..."
sleep 10
for i in {1..30}; do
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo "服务健康检查通过"
        break
    fi
    echo "等待服务启动... ($i/30)"
    sleep 2
done

# 8. 禁用维护模式
echo "步骤 8: 禁用维护模式..."
rm -f /opt/nautilus/backend/MAINTENANCE_MODE

# 9. 通知用户
echo "步骤 9: 发送完成通知..."
curl -X POST http://localhost:8000/api/admin/maintenance \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "message": "系统维护已完成"}'

echo "=== 变更实施完成 ==="
```

### 3.4 回滚流程

```bash
#!/bin/bash
# 变更回滚脚本

set -e

CHANGE_ID="$1"
BACKUP_DIR="/opt/nautilus/backups/change_${CHANGE_ID}"

echo "=== 开始回滚变更 ==="
echo "变更ID: $CHANGE_ID"
echo "时间: $(date)"

# 1. 验证备份存在
if [ ! -d "$BACKUP_DIR" ]; then
    echo "错误: 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

# 2. 停止服务
echo "步骤 1: 停止服务..."
systemctl stop nautilus-backend
systemctl stop nautilus-nexus

# 3. 恢复代码
echo "步骤 2: 恢复代码..."
rsync -av "$BACKUP_DIR/backend/" /opt/nautilus/backend/

# 4. 恢复数据库
echo "步骤 3: 恢复数据库..."
sudo -u postgres psql -d nautilus_prod < "$BACKUP_DIR/database.sql"

# 5. 恢复配置
echo "步骤 4: 恢复配置..."
cp "$BACKUP_DIR/.env" /opt/nautilus/backend/.env

# 6. 启动服务
echo "步骤 5: 启动服务..."
systemctl start nautilus-backend
systemctl start nautilus-nexus

# 7. 验证
echo "步骤 6: 验证回滚..."
sleep 10
curl -s http://localhost:8000/health

echo "=== 回滚完成 ==="
```

---

## 应急响应流程

### 4.1 故障分级

| 级别 | 定义 | 响应时间 | 解决时间 | 通知范围 |
|------|------|---------|---------|---------|
| P0 - 紧急 | 服务完全不可用 | 5 分钟 | 1 小时 | 全员 |
| P1 - 严重 | 核心功能不可用 | 15 分钟 | 4 小时 | 技术团队 |
| P2 - 重要 | 部分功能受影响 | 30 分钟 | 8 小时 | 运维团队 |
| P3 - 一般 | 轻微影响 | 1 小时 | 24 小时 | 值班人员 |

### 4.2 应急响应流程

#### 4.2.1 P0 级故障响应

```bash
#!/bin/bash
# P0 级故障应急响应脚本

echo "=== P0 级故障应急响应 ==="
echo "时间: $(date)"

# 1. 立即通知
echo "1. 发送紧急通知..."
# 发送短信、邮件、钉钉等通知

# 2. 快速诊断
echo "2. 快速诊断..."
echo "检查服务状态:"
systemctl status nautilus-backend
systemctl status postgresql
systemctl status redis

echo "检查端口监听:"
netstat -tlnp | grep -E '(8000|5432|6379)'

echo "检查最近错误:"
journalctl -u nautilus-backend --since "10 minutes ago" --priority=err

# 3. 尝试快速恢复
echo "3. 尝试快速恢复..."
systemctl restart nautilus-backend

# 4. 验证恢复
sleep 5
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "服务已恢复"
else
    echo "服务未恢复，需要进一步诊断"
fi
```

### 4.3 常见故障处理

详见 [INCIDENT_RESPONSE_GUIDE.md](INCIDENT_RESPONSE_GUIDE.md)

---

## 系统维护

### 5.1 定期维护计划

| 维护项目 | 频率 | 执行时间 | 负责人 |
|---------|------|---------|--------|
| 服务健康检查 | 每日 | 09:00 | 值班运维 |
| 日志检查 | 每日 | 10:00 | 值班运维 |
| 数据库备份 | 每日 | 02:00 | 自动任务 |
| 数据库优化 | 每周 | 周日 03:00 | 自动任务 |
| 系统更新 | 每月 | 第一个周日 | 运维负责人 |
| 安全审计 | 每季度 | 季度末 | 安全团队 |

### 5.2 备份策略

详见 [BACKUP_RECOVERY_GUIDE.md](BACKUP_RECOVERY_GUIDE.md)

---

## 安全管理

### 6.1 访问控制

```bash
# 1. SSH 访问控制
# 仅允许密钥认证
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 2. 防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 3. 数据库访问限制
# 编辑 /etc/postgresql/15/main/pg_hba.conf
# 仅允许本地和特定 IP 访问
```

### 6.2 密钥管理

详见 [KEY_MANAGEMENT_GUIDE.md](KEY_MANAGEMENT_GUIDE.md)

---

## 容量规划

### 7.1 资源监控指标

| 资源 | 当前使用 | 警告阈值 | 严重阈值 | 扩容计划 |
|------|---------|---------|---------|---------|
| CPU | 30% | 70% | 85% | 增加实例 |
| 内存 | 40% | 75% | 90% | 增加内存 |
| 磁盘 | 25% | 70% | 85% | 扩展存储 |
| 数据库连接 | 20/100 | 70/100 | 90/100 | 增加连接池 |

### 7.2 扩容流程

详见 [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)

---

## 文档管理

### 8.1 运维文档清单

- [x] OPERATIONS_MANUAL.md - 运维完整手册（本文档）
- [x] MONITORING_OPERATIONS_GUIDE.md - 监控和告警指南
- [x] BACKUP_RECOVERY_GUIDE.md - 备份和恢复指南
- [x] PERFORMANCE_TUNING_GUIDE.md - 性能调优指南
- [x] INCIDENT_RESPONSE_GUIDE.md - 故障处理手册
- [x] OPERATIONS_CHECKLIST.md - 运维检查清单

### 8.2 文档更新流程

1. 发现文档需要更新
2. 创建文档更新分支
3. 更新文档内容
4. 技术审核
5. 合并到主分支
6. 通知相关人员

---

## 附录

### A. 联系方式

| 角色 | 姓名 | 电话 | 邮箱 | 备注 |
|------|------|------|------|------|
| 技术负责人 | - | - | - | 7x24 |
| 运维负责人 | - | - | - | 工作时间 |
| 值班运维 | - | - | - | 轮班 |
| DBA | - | - | - | 工作时间 |

### B. 外部服务

| 服务 | 提供商 | 联系方式 | SLA |
|------|--------|---------|-----|
| 云服务器 | - | - | 99.95% |
| 区块链 RPC | Infura | support@infura.io | 99.9% |
| CDN | - | - | 99.9% |
| 监控告警 | - | - | - |

---

**文档版本**: 1.0
**最后更新**: 2026-02-26
**下次审核**: 2026-03-26
