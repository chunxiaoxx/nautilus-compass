# ✅ 服务器升级操作清单

**准备时间**: 2026-02-28 11:31
**备份状态**: ✅ 已完成

---

## 📦 备份文件清单

已备份的文件：
- ✅ 配置文件: `/tmp/nautilus_config_backup.tar.gz` (844 bytes)
- ✅ Docker镜像: `/tmp/nautilus_api_image.tar.gz` (101MB)
- ✅ 容器状态: `/tmp/docker_status.txt` (586 bytes)

---

## 🚀 升级步骤（按顺序执行）

### 第1步：停止服务

```bash
ssh cloud -p 24860 "cd /opt/nautilus && docker compose -f docker-compose.simple.yml down"
```

**预期结果**: 3个容器停止

---

### 第2步：在阿里云控制台升级

1. **登录阿里云控制台**
   - 网址: https://ecs.console.aliyun.com

2. **找到实例**
   - 实例ID: 43.160.239.61
   - 当前配置: 2核4GB 60GB

3. **停止实例**
   - 点击"停止"按钮
   - 等待状态变为"已停止"

4. **升级配置**
   - 点击"升降配" → "升级配置"
   - 选择: **4核8GB**
   - 确认费用并支付

5. **扩容磁盘**
   - 进入"云盘"管理
   - 选择系统盘
   - 点击"扩容"
   - 输入新容量: **100GB**
   - 确认并支付

6. **启动实例**
   - 返回实例列表
   - 点击"启动"
   - 等待状态变为"运行中"

---

### 第3步：扩展文件系统

```bash
# 扩展分区
ssh cloud -p 24860 "sudo growpart /dev/vda 2"

# 扩展文件系统
ssh cloud -p 24860 "sudo resize2fs /dev/vda2"

# 验证磁盘空间
ssh cloud -p 24860 "df -h /"
```

**预期结果**: 磁盘从59GB扩展到99GB

---

### 第4步：验证系统资源

```bash
ssh cloud -p 24860 "echo '=== CPU ===' && lscpu | grep 'CPU(s):' && echo '' && echo '=== 内存 ===' && free -h && echo '' && echo '=== 磁盘 ===' && df -h /"
```

**预期结果**:
- CPU: 4核
- 内存: 8GB
- 磁盘: 99GB

---

### 第5步：启动服务

```bash
ssh cloud -p 24860 "cd /opt/nautilus && docker compose -f docker-compose.simple.yml up -d"
```

**预期结果**: 3个容器启动

---

### 第6步：等待服务就绪

```bash
# 等待30秒
sleep 30

# 检查容器状态
ssh cloud -p 24860 "docker ps"
```

**预期结果**: 3个容器都是"Up"状态

---

### 第7步：验证服务

```bash
# 测试API根路径
curl http://43.160.239.61:8000/

# 测试健康检查
curl http://43.160.239.61:8000/health
```

**预期结果**:
- 根路径返回API信息
- 健康检查返回状态

---

## ✅ 验证清单

完成后勾选：

### 系统资源
- [ ] CPU: 4核
- [ ] 内存: 8GB
- [ ] 磁盘: 100GB
- [ ] 文件系统已扩展

### Docker服务
- [ ] Docker服务运行正常
- [ ] nautilus-api容器运行
- [ ] nautilus-postgres容器运行
- [ ] nautilus-redis容器运行

### API服务
- [ ] 根路径响应正常
- [ ] 健康检查通过
- [ ] Redis连接正常

---

## 🚨 如果出现问题

### 问题1: 容器无法启动

```bash
# 查看日志
ssh cloud -p 24860 "docker logs nautilus-api --tail=50"

# 重启容器
ssh cloud -p 24860 "docker restart nautilus-api"
```

### 问题2: 磁盘未扩展

```bash
# 重新扩展
ssh cloud -p 24860 "sudo growpart /dev/vda 2 && sudo resize2fs /dev/vda2"
```

### 问题3: 服务无响应

```bash
# 完全重启
ssh cloud -p 24860 "cd /opt/nautilus && docker compose -f docker-compose.simple.yml restart"
```

---

## 📊 升级后优化（可选）

### 优化PostgreSQL

```bash
ssh cloud -p 24860 "docker exec nautilus-postgres psql -U nautilus -c \"ALTER SYSTEM SET shared_buffers = '2GB';\""
ssh cloud -p 24860 "docker exec nautilus-postgres psql -U nautilus -c \"ALTER SYSTEM SET effective_cache_size = '6GB';\""
ssh cloud -p 24860 "docker restart nautilus-postgres"
```

### 优化Redis

```bash
ssh cloud -p 24860 "docker exec nautilus-redis redis-cli CONFIG SET maxmemory 2gb"
ssh cloud -p 24860 "docker exec nautilus-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru"
```

---

## 📝 升级记录

- **开始时间**: ___________
- **停止服务**: ___________
- **升级配置**: ___________
- **启动服务**: ___________
- **验证完成**: ___________
- **总耗时**: ___________

---

## 💡 提示

1. **最佳时间**: 建议在用户少的时候升级（如凌晨）
2. **预计时间**: 整个过程约15-20分钟
3. **服务中断**: 升级期间服务会中断
4. **费用增加**: 约50-100元/月

---

**准备状态**: ✅ 就绪
**备份状态**: ✅ 已完成
**可以开始升级**: ✅ 是

**现在可以开始第1步：停止服务！**
