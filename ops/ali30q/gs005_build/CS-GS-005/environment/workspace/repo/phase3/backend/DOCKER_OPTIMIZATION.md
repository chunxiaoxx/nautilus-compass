# Nexus Server Docker 配置优化说明

## 优化内容总结

### 1. Dockerfile优化

**优化前:**
- 单阶段构建
- 使用root用户运行
- 镜像较大

**优化后:**
- ✅ 多阶段构建，减小镜像大小
- ✅ 创建非root用户（nexus），提高安全性
- ✅ 优化层缓存，加快构建速度
- ✅ 增加健康检查启动时间（start_period: 10s）

**关键改进:**
```dockerfile
# 多阶段构建
FROM python:3.13-slim as builder
# ... 构建依赖

FROM python:3.13-slim
# 创建非root用户
RUN useradd -m -u 1000 nexus
USER nexus
```

### 2. docker-compose.yml优化

**优化前:**
- 硬编码环境变量
- 缺少日志配置
- 网络配置简单

**优化后:**
- ✅ 支持环境变量文件（.env）
- ✅ 添加日志轮转配置
- ✅ 添加卷挂载支持
- ✅ 优化网络配置（自定义子网）
- ✅ 增加镜像标签

**关键改进:**
```yaml
environment:
  - MAX_AGENTS=${MAX_AGENTS:-100}  # 支持环境变量
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
volumes:
  - nexus-logs:/app/logs  # 持久化日志
```

### 3. 新增配置文件

#### docker-compose.dev.yml
- 开发环境专用配置
- 代码热重载（挂载源代码）
- 较低的资源限制
- DEBUG日志级别

#### docker-compose.prod.yml
- 生产环境专用配置
- 高可用配置（支持多副本）
- 更高的资源限制
- 安全加固（no-new-privileges）
- 滚动更新策略

### 4. .dockerignore优化

**优化前:**
- 排除了部分必要文件
- 规则不够精细

**优化后:**
- ✅ 保留部署文档
- ✅ 排除所有测试和报告文件
- ✅ 排除开发工具配置
- ✅ 减小构建上下文大小

### 5. 新增部署脚本

#### deploy.sh (Linux/Mac)
- 交互式菜单
- 自动化部署流程
- 健康检查
- 错误处理

#### deploy.bat (Windows)
- Windows批处理脚本
- 与Linux版本功能一致
- 适配Windows命令

### 6. 环境变量配置

#### .env.example
- 提供配置模板
- 清晰的变量说明
- 开发/生产环境示例

## 镜像大小优化

**优化措施:**
1. 多阶段构建，只复制必要的依赖
2. 使用 `python:3.13-slim` 基础镜像
3. 清理apt缓存
4. 不包含测试文件和文档

**预期效果:**
- 基础镜像: ~150MB
- 依赖层: ~100MB
- 应用代码: ~1MB
- **总计: ~250MB**（相比单阶段构建减少约40%）

## 安全性增强

1. **非root用户运行**
   - 创建专用用户 `nexus`
   - UID: 1000
   - 限制权限

2. **安全选项（生产环境）**
   ```yaml
   security_opt:
     - no-new-privileges:true
   read_only: false
   ```

3. **资源限制**
   - CPU限制：防止资源耗尽
   - 内存限制：防止OOM
   - 日志大小限制：防止磁盘占满

## 性能优化

1. **构建缓存**
   - 优化层顺序
   - 依赖层独立
   - 代码层最后

2. **运行时优化**
   - PYTHONUNBUFFERED=1：实时日志
   - PYTHONDONTWRITEBYTECODE=1：不生成.pyc
   - PIP_NO_CACHE_DIR=1：减小镜像大小

3. **网络优化**
   - 自定义网络
   - 固定子网
   - 支持服务发现

## 可维护性提升

1. **多环境支持**
   - 开发环境：快速迭代
   - 生产环境：稳定可靠
   - 默认配置：快速测试

2. **自动化脚本**
   - 一键部署
   - 健康检查
   - 日志查看
   - 资源清理

3. **文档完善**
   - 部署指南
   - 故障排查
   - 测试清单
   - 配置说明

## 配置对比

| 特性 | 开发环境 | 默认配置 | 生产环境 |
|------|---------|---------|---------|
| MAX_AGENTS | 50 | 100 | 200 |
| MAX_QUEUE_SIZE | 500 | 1000 | 2000 |
| LOG_LEVEL | debug | info | warning |
| CPU限制 | 2核 | 2核 | 4核 |
| 内存限制 | 1GB | 1GB | 2GB |
| 副本数 | 1 | 1 | 2 |
| 代码挂载 | ✅ | ❌ | ❌ |
| 安全加固 | ❌ | ❌ | ✅ |

## 使用建议

### 开发阶段
```bash
docker-compose -f docker-compose.dev.yml up -d
```
- 代码修改自动生效
- 详细的调试日志
- 较低的资源占用

### 测试阶段
```bash
docker-compose up -d
```
- 接近生产环境
- 完整的功能测试
- 性能测试

### 生产部署
```bash
docker-compose -f docker-compose.prod.yml up -d
```
- 高可用配置
- 安全加固
- 监控和日志

## 后续优化建议

1. **监控集成**
   - Prometheus metrics
   - Grafana仪表板
   - 告警规则

2. **日志聚合**
   - ELK Stack
   - Loki
   - CloudWatch

3. **CI/CD集成**
   - 自动构建
   - 自动测试
   - 自动部署

4. **负载均衡**
   - Nginx反向代理
   - Traefik
   - HAProxy

5. **服务编排**
   - Kubernetes部署
   - Docker Swarm
   - Helm Charts
