# 🚀 Nautilus服务器升级指南

**当前配置**: 2核4GB 60GB
**推荐配置**: 4核8GB 100GB
**升级时间**: 2026-02-28

---

## 📊 当前状态

### 资源使用
- **CPU**: 2核
- **内存**: 3.6GB (使用1.4GB, 39%)
- **磁盘**: 59GB (使用39GB, 69%)
- **运行时间**: 4天12小时

### 服务状态
- ✅ nautilus-api (运行11小时)
- ✅ nautilus-postgres (运行11小时)
- ✅ nautilus-redis (运行11小时)

---

## ✅ 升级建议

### 推荐配置

**方案A: 标准升级（推荐）**
- CPU: 2核 → 4核
- 内存: 4GB → 8GB
- 磁盘: 60GB → 100GB
- 预计费用: +50-100元/月

**方案B: 高性能升级**
- CPU: 2核 → 8核
- 内存: 4GB → 16GB
- 磁盘: 60GB → 200GB
- 预计费用: +150-200元/月

**方案C: 经济升级**
- CPU: 2核 → 2核
- 内存: 4GB → 8GB
- 磁盘: 60GB → 100GB
- 预计费用: +30-50元/月

---

## 📋 升级前准备

### 1. 备份数据（必须！）

```bash
# 上传备份脚本
scp scripts/backup_before_upgrade.sh cloud:/tmp/

# 执行备份
ssh cloud -p 24860 "bash /tmp/backup_before_upgrade.sh"
```

### 2. 停止服务

```bash
ssh cloud -p 24860 "cd /opt/nautilus && docker compose -f docker-compose.simple.yml down"
```

### 3. 记录重要信息

```bash
# 记录环境变量
ssh cloud -p 24860 "cat /opt/nautilus/.env" > backup_env.txt

# 记录Docker配置
ssh cloud -p 24860 "cat /opt/nautilus/docker-compose.simple.yml" > backup_compose.yml
```

---

## 🔧 升级步骤

### 阿里云控制台操作

1. **登录阿里云控制台**
   - 进入ECS实例管理

2. **停止实例**
   - 选择实例 43.160.239.61
   - 点击"停止"
   - 等待状态变为"已停止"

3. **升级配置**
   - 点击"升降配"
   - 选择"升级配置"
   - 选择新配置（4核8GB）
   - 确认费用
   - 点击"确定"

4. **扩容磁盘**
   - 进入"云盘"管理
   - 选择系统盘
   - 点击"扩容"
   - 输入新容量（100GB）
   - 确认并支付

5. **启动实例**
   - 返回实例列表
   - 点击"启动"
   - 等待状态变为"运行中"

---

## 🔄 升级后操作

### 1. 验证系统

```bash
# 检查系统信息
ssh cloud -p 24860 "free -h && df -h && lscpu | grep 'CPU(s)'"
```

### 2. 扩展文件系统（重要！）

```bash
# 扩展分区
ssh cloud -p 24860 "sudo growpart /dev/vda 2"

# 扩展文件系统
ssh cloud -p 24860 "sudo resize2fs /dev/vda2"

# 验证
ssh cloud -p 24860 "df -h /"
```

### 3. 启动服务

```bash
# 启动Docker服务
ssh cloud -p 24860 "cd /opt/nautilus && docker compose -f docker-compose.simple.yml up -d"

# 等待30秒
sleep 30

# 检查容器状态
ssh cloud -p 24860 "docker ps"
```

### 4. 验证服务

```bash
# 测试API
curl http://43.160.239.61:8000/

# 测试健康检查
curl http://43.160.239.61:8000/health
```

---

## ✅ 验证清单

### 系统验证
- [ ] CPU核心数正确
- [ ] 内存容量正确
- [ ] 磁盘容量正确
- [ ] 文件系统已扩展

### 服务验证
- [ ] Docker服务运行正常
- [ ] nautilus-api容器运行
- [ ] nautilus-postgres容器运行
- [ ] nautilus-redis容器运行

### 功能验证
- [ ] API根路径响应正常
- [ ] 健康检查通过
- [ ] 数据库连接正常
- [ ] Redis连接正常

---

## 🚨 回滚方案

如果升级后出现问题：

### 方案1: 重启服务

```bash
ssh cloud -p 24860 "cd /opt/nautilus && docker compose -f docker-compose.simple.yml restart"
```

### 方案2: 恢复备份

```bash
# 恢复数据库
ssh cloud -p 24860 "cat /tmp/nautilus_backup_*.sql | docker exec -i nautilus-postgres psql -U nautilus nautilus"

# 恢复Redis
ssh cloud -p 24860 "docker cp /tmp/redis_backup_*.rdb nautilus-redis:/data/dump.rdb && docker restart nautilus-redis"
```

### 方案3: 降级配置

通过阿里云控制台降回原配置

---

## 📊 升级后优化

### 1. 调整Docker资源限制

```yaml
# docker-compose.simple.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 2. 优化PostgreSQL配置

```bash
# 编辑PostgreSQL配置
ssh cloud -p 24860 "docker exec nautilus-postgres bash -c 'echo \"shared_buffers = 2GB\" >> /var/lib/postgresql/data/postgresql.conf'"
ssh cloud -p 24860 "docker exec nautilus-postgres bash -c 'echo \"effective_cache_size = 6GB\" >> /var/lib/postgresql/data/postgresql.conf'"
ssh cloud -p 24860 "docker restart nautilus-postgres"
```

### 3. 优化Redis配置

```bash
# 设置最大内存
ssh cloud -p 24860 "docker exec nautilus-redis redis-cli CONFIG SET maxmemory 2gb"
ssh cloud -p 24860 "docker exec nautilus-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru"
```

---

## 💰 费用估算

### 方案A（推荐）
- 原配置: 2核4GB 60GB ≈ 100元/月
- 新配置: 4核8GB 100GB ≈ 150-200元/月
- 增加费用: 50-100元/月

### 预期收益
- CPU性能提升: 2倍
- 内存容量提升: 2倍
- 磁盘容量提升: 67%
- 可支持更多并发用户
- 更好的性能表现

---

## 📝 注意事项

### 升级期间
1. **服务会中断**: 预计10-20分钟
2. **选择低峰时段**: 建议凌晨或用户少的时候
3. **提前通知**: 如有用户，提前通知维护时间

### 升级后
1. **监控性能**: 观察1-2天
2. **检查日志**: 确保无异常
3. **备份策略**: 建立定期备份

---

## 🎯 快速升级命令

```bash
# 1. 备份
ssh cloud -p 24860 "bash /tmp/backup_before_upgrade.sh"

# 2. 停止服务
ssh cloud -p 24860 "cd /opt/nautilus && docker compose -f docker-compose.simple.yml down"

# 3. 在阿里云控制台升级配置

# 4. 扩展文件系统
ssh cloud -p 24860 "sudo growpart /dev/vda 2 && sudo resize2fs /dev/vda2"

# 5. 启动服务
ssh cloud -p 24860 "cd /opt/nautilus && docker compose -f docker-compose.simple.yml up -d"

# 6. 验证
ssh cloud -p 24860 "docker ps && free -h && df -h"
curl http://43.160.239.61:8000/health
```

---

## ✅ 总结

### 升级优势
- ✅ 性能提升2倍
- ✅ 支持更多用户
- ✅ 更好的稳定性
- ✅ 为未来扩展预留空间

### 风险控制
- ✅ 完整备份
- ✅ 详细步骤
- ✅ 回滚方案
- ✅ 验证清单

**建议**: 选择方案A（4核8GB 100GB），性价比最高！

---

**创建时间**: 2026-02-28 01:30
**状态**: ✅ 准备就绪
**建议**: 现在可以升级！
