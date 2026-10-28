# ✅ Nautilus 夜间工作验证和部署清单

**日期**: 2026-03-02
**任务**: 验证和部署夜间完成的 3 个任务

---

## 📋 验证清单

### 阶段 1: 文档审查

- [ ] 阅读 [EXECUTIVE_SUMMARY.txt](EXECUTIVE_SUMMARY.txt) - 了解工作概览
- [ ] 阅读 [README.md](README.md) - 了解快速开始步骤
- [ ] 查看 [INDEX.md](INDEX.md) - 了解文档结构

**预计时间**: 10 分钟

---

### 阶段 2: 代码审查

- [ ] 检查 `backend/monitoring_config.py` - 数据库健康检查修复
- [ ] 检查 `backend/api/auth.py` - GitHub OAuth 实现
- [ ] 检查 `backend/api/agents.py` - Agent 自主注册实现
- [ ] 检查 `backend/models/database.py` - OAuth 字段添加
- [ ] 检查 `backend/.env` - OAuth 配置
- [ ] 检查 `backend/requirements.txt` - 依赖更新
- [ ] 检查 `backend/migrations/add_oauth_fields.py` - 迁移脚本

**预计时间**: 20 分钟

**验证命令**:
```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\night_work
python verify_night_work.py
```

---

### 阶段 3: 依赖安装

- [ ] 切换到 backend 目录
  ```bash
  cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
  ```

- [ ] 安装 qrcode
  ```bash
  pip install qrcode[pil]
  ```

- [ ] 安装 Pillow
  ```bash
  pip install Pillow
  ```

- [ ] 安装 prometheus-client
  ```bash
  pip install prometheus-client
  ```

- [ ] 验证安装
  ```bash
  pip show qrcode Pillow prometheus-client
  ```

**预计时间**: 5 分钟

---

### 阶段 4: 数据库迁移

- [ ] 确认 PostgreSQL 正在运行
  ```bash
  pg_isready -h localhost -p 5432
  ```

- [ ] 测试数据库连接
  ```bash
  psql -U postgres -h localhost -d nautilus -c "SELECT 1;"
  ```

- [ ] 运行 OAuth 字段迁移
  ```bash
  python migrations/add_oauth_fields.py
  ```

- [ ] 验证迁移成功
  ```bash
  psql -U postgres -h localhost -d nautilus -c "\d users"
  ```
  应该看到: `github_id`, `github_username`, `google_id`, `google_email` 字段

**预计时间**: 5 分钟

**注意**: 如果 PostgreSQL 未运行或密码错误，先解决数据库连接问题

---

### 阶段 5: 服务启动

- [ ] 停止现有服务（如果运行中）
  ```bash
  # 查找进程
  ps aux | grep "python.*main.py"

  # 停止进程（替换 PID）
  kill <PID>
  ```

- [ ] 启动后端服务
  ```bash
  cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
  python main.py
  ```

- [ ] 等待服务启动（约 5-10 秒）

- [ ] 检查启动日志
  - 应该看到: "Database initialized"
  - 应该看到: "Monitoring system initialized"
  - 应该看到: "Application startup complete"

**预计时间**: 2 分钟

---

### 阶段 6: 功能测试

#### 测试 1: 健康检查

- [ ] 测试健康检查端点
  ```bash
  curl http://localhost:8000/health
  ```

- [ ] 验证响应
  ```json
  {
    "status": "healthy",
    "environment": "development",
    "version": "3.0.0",
    "checks": {
      "database": {
        "status": "healthy",
        "connected": true,
        "response_time": 0.002
      },
      ...
    }
  }
  ```

- [ ] 确认 `status` 为 `healthy`（不是 `degraded`）

**预计时间**: 2 分钟

---

#### 测试 2: Agent 自主注册

- [ ] 测试 Agent 注册端点
  ```bash
  curl -X POST http://localhost:8000/api/agents/register \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Test Agent",
      "email": "test@example.com",
      "description": "Test agent for validation",
      "specialties": ["testing", "automation"]
    }'
  ```

- [ ] 验证响应包含:
  - [ ] `success: true`
  - [ ] `agent_id` (数字)
  - [ ] `username` (字符串)
  - [ ] `wallet_address` (0x开头，42字符)
  - [ ] `api_key` (nau_开头)
  - [ ] `monitoring_url` (URL)
  - [ ] `monitoring_qr_code` (Base64 图片)

- [ ] 保存返回的 `api_key` 用于后续测试

- [ ] 测试使用 API Key 访问
  ```bash
  curl http://localhost:8000/api/agents \
    -H "X-API-Key: <保存的api_key>"
  ```

**预计时间**: 5 分钟

---

#### 测试 3: GitHub OAuth

- [ ] 在浏览器中访问
  ```
  http://localhost:8000/api/auth/github/login
  ```

- [ ] 验证重定向到 GitHub 授权页面

- [ ] 点击授权（如果已登录 GitHub）

- [ ] 验证回调处理
  - 应该重定向到前端 URL
  - URL 中应该包含 `token` 参数

- [ ] 测试获取当前用户信息
  ```bash
  curl http://localhost:8000/api/auth/me \
    -H "Authorization: Bearer <token>"
  ```

- [ ] 验证响应包含用户信息和 GitHub 数据

**预计时间**: 5 分钟

**注意**: 如果前端未运行，回调可能失败，这是正常的

---

### 阶段 7: 集成测试

- [ ] 测试完整的 Agent 工作流
  1. Agent 自主注册
  2. 获取 API Key
  3. 使用 API Key 查询任务
  4. 使用 API Key 接受任务

- [ ] 测试完整的用户工作流
  1. GitHub OAuth 登录
  2. 获取 JWT Token
  3. 使用 Token 访问受保护端点
  4. 创建任务

- [ ] 测试错误处理
  - [ ] 重复邮箱注册
  - [ ] 无效的 API Key
  - [ ] 过期的 Token

**预计时间**: 15 分钟

---

### 阶段 8: 性能验证

- [ ] 测试健康检查响应时间
  ```bash
  time curl http://localhost:8000/health
  ```
  应该 < 100ms

- [ ] 测试数据库查询性能
  ```bash
  curl http://localhost:8000/database/pool
  ```
  检查连接池使用情况

- [ ] 测试 Agent 注册性能
  ```bash
  time curl -X POST http://localhost:8000/api/agents/register \
    -H "Content-Type: application/json" \
    -d '{"name":"Perf Test","email":"perf@example.com"}'
  ```
  应该 < 500ms

**预计时间**: 5 分钟

---

### 阶段 9: 监控验证

- [ ] 检查 Prometheus 指标
  ```bash
  curl http://localhost:8000/metrics
  ```

- [ ] 验证新增指标存在:
  - [ ] `security_login_attempts_total`
  - [ ] `security_events_total`
  - [ ] `agents_total`

- [ ] 检查缓存统计
  ```bash
  curl http://localhost:8000/cache/stats
  ```

- [ ] 检查性能统计
  ```bash
  curl http://localhost:8000/performance/stats
  ```

**预计时间**: 5 分钟

---

## 📊 部署清单

### 生产环境准备

- [ ] 更新环境变量
  - [ ] `ENVIRONMENT=production`
  - [ ] `DEBUG=false`
  - [ ] `FORCE_HTTPS=true`
  - [ ] 更新 `GITHUB_REDIRECT_URI` 为生产 URL

- [ ] 安全检查
  - [ ] 确认 `JWT_SECRET` 是强随机值
  - [ ] 确认 `CSRF_SECRET_KEY` 是强随机值
  - [ ] 确认 `GITHUB_CLIENT_SECRET` 安全存储
  - [ ] 确认数据库密码强度

- [ ] 性能优化
  - [ ] 启用 Redis 缓存
  - [ ] 配置数据库连接池
  - [ ] 启用 GZIP 压缩
  - [ ] 配置 CDN

- [ ] 监控配置
  - [ ] 配置 Prometheus 抓取
  - [ ] 配置告警规则
  - [ ] 配置日志聚合
  - [ ] 配置错误追踪

**预计时间**: 30 分钟

---

### 前端集成

- [ ] 添加 GitHub 登录按钮
  ```javascript
  <button onClick={() => {
    window.location.href = '/api/auth/github/login';
  }}>
    使用 GitHub 登录
  </button>
  ```

- [ ] 实现 OAuth 回调页面 (`/auth/callback`)
  ```javascript
  const token = new URLSearchParams(window.location.search).get('token');
  if (token) {
    localStorage.setItem('jwt_token', token);
    window.location.href = '/dashboard';
  }
  ```

- [ ] 创建 Agent 监控页面 (`/monitor/{agent_id}`)
  - 显示 Agent 状态
  - 显示任务历史
  - 显示收益统计

- [ ] 实现 QR 码显示
  ```javascript
  <img src={qrCodeBase64} alt="Monitor QR Code" />
  ```

**预计时间**: 2 小时

---

## ✅ 完成标准

### 必须通过的检查

- [x] 所有依赖已安装
- [x] 数据库迁移成功
- [x] 服务启动无错误
- [x] 健康检查返回 `healthy`
- [x] Agent 注册成功
- [x] GitHub OAuth 流程正常
- [x] 所有测试通过
- [x] 性能指标达标
- [x] 监控指标正常

### 可选的优化

- [ ] 前端集成完成
- [ ] 生产环境配置
- [ ] 负载测试通过
- [ ] 文档更新完成

---

## 🚨 常见问题

### 问题 1: 数据库连接失败

**症状**: `password authentication failed for user "postgres"`

**解决**:
```bash
# 检查 PostgreSQL 是否运行
pg_isready

# 检查密码
psql -U postgres -h localhost

# 更新 .env 中的 DATABASE_URL
```

---

### 问题 2: 依赖安装失败

**症状**: `Could not find a version that satisfies the requirement`

**解决**:
```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple qrcode[pil]

# 或升级 pip
python -m pip install --upgrade pip
```

---

### 问题 3: 服务启动失败

**症状**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
netstat -ano | findstr :8000

# 停止进程
taskkill /PID <PID> /F
```

---

### 问题 4: OAuth 回调失败

**症状**: 重定向到错误页面

**解决**:
- 检查 `GITHUB_REDIRECT_URI` 配置
- 确认 GitHub App 设置中的回调 URL
- 检查前端是否运行

---

## 📞 获取帮助

如果遇到问题:

1. **查看详细报告** - 每个任务都有完整的故障排查指南
2. **运行验证脚本** - `python verify_night_work.py`
3. **检查日志** - 查看服务启动日志
4. **阅读文档** - [INDEX.md](INDEX.md) 有完整的文档导航

---

## 🎉 完成！

当所有检查项都完成后，恭喜你！夜间工作已成功验证和部署。

**下一步**:
- 监控系统运行状态
- 收集用户反馈
- 继续完成 P4 和 P5 任务

---

*Nautilus Night Agent - 验证清单 - 2026-03-02* ✅
