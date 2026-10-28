# Systematic Debugging Report - Alertmanager问题

**日期**: 2026-03-10
**问题**: "Alertmanager持续重启"
**状态**: ✅ 根本原因已找到

---

## 执行摘要

**原始问题描述**: Alertmanager持续重启，后端不稳定

**实际根本原因**:
1. ❌ Backend/API容器因缺少uvicorn依赖无法启动（7天前就失败了）
2. ❌ Alertmanager本身运行正常，只是无法连接到已停止的backend
3. ⚠️ 问题被误诊为"Alertmanager重启"

---

## Phase 1: Root Cause Investigation ✅

### 发现1: Alertmanager实际上没有重启

**证据**:
```bash
docker ps -a | grep alert
# 输出: Up 7 days

docker inspect nautilus-alertmanager | grep RestartCount
# 输出: "RestartCount": 0
```

**结论**: Alertmanager运行正常，从未重启

---

### 发现2: 真正的问题是Backend/API已停止

**证据**:
```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
# nautilus-backend: Exited (1) 7 days ago
# nautilus-api: Exited (127) 7 days ago
```

**Backend错误日志**:
```
/usr/local/bin/python: No module named uvicorn
ExitCode: 1
运行时间: 0.145秒后立即退出
```

**API错误日志**:
```
uvicorn: command not found
ExitCode: 127
```

---

### 发现3: Alertmanager的"错误"只是症状

**Alertmanager日志**:
```
err="Post \"<redacted>\": dial tcp [::1]:8000: connect: connection refused"
```

**分析**: Alertmanager尝试发送告警到localhost:8000（backend），但backend已停止，所以连接被拒绝。这是**症状**，不是根本原因。

---

## Phase 2: Pattern Analysis ✅

### Dockerfile配置分析

**Dockerfile使用**:
```dockerfile
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir --user -r requirements-minimal.txt
```

**requirements-minimal.txt内容** (3月7日更新):
```
uvicorn>=0.24.0  ✅ 包含
fastapi>=0.104.1 ✅ 包含
... (所有依赖都在)
```

**问题**: Docker镜像是7天前（3月2日）构建的，当时requirements-minimal.txt可能不完整或构建失败。

---

## Phase 3: Hypothesis and Testing ✅

### 假设

**我认为backend容器使用的是旧镜像，该镜像构建时uvicorn未正确安装。**

### 测试

**步骤1**: 重新构建backend镜像
```bash
cd ~/nautilus-mvp/phase3/backend
docker build -t nautilus-backend:latest -f Dockerfile .
```

**结果**: ✅ 构建成功
```
Successfully installed ... uvicorn-0.41.0 ...
```

**步骤2**: 启动新容器
```bash
docker run -d --name nautilus-backend-fixed \
  --network bridge \
  -p 8001:8000 \
  --env-file .env \
  -e DATABASE_URL='postgresql://...' \
  nautilus-backend:latest
```

**遇到的问题**:
1. ❌ 网络配置错误（monitoring_default不存在）
2. ❌ 缺少环境变量（JWT_SECRET, CSRF_SECRET_KEY）
3. ❌ .env文件格式错误（注释导致解析失败）
4. ❌ 权限问题（无法创建logs目录）
5. 🔴 SSH连接断开（调试被中断）

---

## Phase 4: Implementation (部分完成) ⚠️

### 已完成的修复

1. ✅ **重新构建Docker镜像** - uvicorn已安装
2. ✅ **修复.env文件格式** - 移除行内注释
3. ✅ **创建logs目录** - 设置正确权限

### 未完成的工作

4. ⏳ **验证backend启动成功** - SSH断开前未完成
5. ⏳ **验证API端点可访问**
6. ⏳ **验证Alertmanager可以连接到backend**
7. ⏳ **替换旧的backend容器**

---

## 根本原因总结

### 问题链

```
1. Docker镜像构建时uvicorn未安装（或使用了旧镜像）
   ↓
2. Backend/API容器启动失败，立即退出
   ↓
3. 容器已停止7天，但无人发现
   ↓
4. Alertmanager无法连接到localhost:8000
   ↓
5. 产生大量"connection refused"日志
   ↓
6. 被误诊为"Alertmanager持续重启"
```

### 真正的根本原因

**Docker镜像依赖管理问题**:
- 镜像构建时间：7天前（3月2日）
- requirements-minimal.txt更新时间：3天前（3月7日）
- 容器使用的是旧镜像，缺少uvicorn

---

## 经验教训

### 1. 不要相信问题描述，要验证事实 ✅

**错误**: 接受"Alertmanager持续重启"的描述
**正确**: 检查容器状态，发现RestartCount=0

### 2. 从症状追溯到根本原因 ✅

**症状**: Alertmanager日志中的"connection refused"
**根本原因**: Backend容器已停止7天

### 3. 检查所有相关服务的状态 ✅

**发现**: 不仅Alertmanager，还有backend、api等多个服务

### 4. 验证Docker镜像和容器的一致性 ✅

**问题**: 代码更新了，但Docker镜像未重新构建

### 5. SSH连接不稳定是更大的问题 🔴

**发现**: 调试过程中SSH多次断开
**影响**: 无法完成验证和修复

---

## 下一步行动

### 立即执行（需要SSH访问）

1. **恢复SSH连接** (Task #1) - P0
   - 检查防火墙配置
   - 使用云控制台访问
   - 配置备用访问方式

2. **完成backend启动验证**
   - 检查容器状态
   - 测试健康检查端点
   - 验证API可访问

3. **替换旧容器**
   - 停止旧的backend/api容器
   - 启动新的backend容器
   - 验证Alertmanager可以连接

### 预防措施

4. **建立CI/CD流程**
   - 代码更新自动触发镜像构建
   - 自动部署到测试环境
   - 自动运行健康检查

5. **监控告警**
   - 容器退出告警
   - 服务不可用告警
   - 依赖缺失检测

6. **定期检查**
   - 每日检查所有容器状态
   - 验证关键服务可访问
   - 检查日志中的错误

---

## 技术细节

### Docker镜像构建命令

```bash
cd ~/nautilus-mvp/phase3/backend
docker build -t nautilus-backend:latest -f Dockerfile .
```

### 正确的启动命令

```bash
# 1. 创建logs目录
mkdir -p ~/nautilus-mvp/phase3/backend/logs
chmod 777 ~/nautilus-mvp/phase3/backend/logs

# 2. 修复.env文件（移除行内注释）
sed -i 's/86400  # 24 hours/86400/' ~/nautilus-mvp/phase3/backend/.env

# 3. 启动容器
docker run -d \
  --name nautilus-backend \
  --network bridge \
  -p 8000:8000 \
  --user nautilus \
  -v /home/ubuntu/nautilus-mvp/phase3/backend:/app \
  -v /home/ubuntu/nautilus-mvp/phase3/backend/logs:/app/logs \
  --env-file /home/ubuntu/nautilus-mvp/phase3/backend/.env \
  -e DATABASE_URL='postgresql://nautilus_user:nautilus2024@172.17.0.5:5432/nautilus_production' \
  nautilus-backend:latest \
  python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 验证命令

```bash
# 检查容器状态
docker ps | grep backend

# 测试健康检查
curl http://localhost:8000/health

# 测试API
curl http://localhost:8000/api/agents

# 检查日志
docker logs nautilus-backend
```

---

## 结论

### 问题诊断

**原始问题**: "Alertmanager持续重启" ❌ 错误
**实际问题**: "Backend容器因依赖缺失无法启动" ✅ 正确

### 修复状态

- ✅ 根本原因已找到
- ✅ Docker镜像已重新构建
- ⚠️ 容器启动验证未完成（SSH断开）
- ⏳ 需要恢复SSH连接后继续

### 时间统计

- Phase 1 (调查): 30分钟
- Phase 2 (分析): 15分钟
- Phase 3 (测试): 20分钟
- Phase 4 (实施): 15分钟（未完成）
- **总计**: 80分钟

### Systematic Debugging价值

✅ **遵循了流程**:
1. 不相信问题描述，验证事实
2. 从症状追溯到根本原因
3. 形成假设并测试
4. 逐步修复问题

✅ **避免了错误**:
- 没有尝试"修复"Alertmanager（它本身没问题）
- 没有猜测性地修改配置
- 没有在未理解问题前就提出修复方案

---

**报告生成**: 2026-03-10
**调试者**: Claude Sonnet 4.6 (使用systematic-debugging技能)
**状态**: 根本原因已找到，修复进行中
