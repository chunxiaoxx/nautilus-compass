# GitHub Actions 工作流说明

本目录包含 Nautilus 后端项目的所有 GitHub Actions 工作流配置。

## 工作流文件

### 1. ci.yml - 持续集成
**用途**: 代码质量检查和测试
**触发**: Push/PR 到 main, develop, feature 分支
**包含**:
- 代码质量检查 (Black, isort, Flake8, Pylint, Mypy)
- 依赖安全检查 (Safety, pip-audit)
- 单元测试 (覆盖率 ≥ 80%)
- 集成测试
- Docker 构建验证

### 2. cd.yml - 持续部署
**用途**: 自动化部署流程
**触发**: Push 到 main, 版本标签, 手动触发
**包含**:
- 构建并推送 Docker 镜像
- 部署到 Staging 环境
- 部署到 Production 环境 (需审批)
- 自动回滚机制

### 3. test.yml - 测试套件
**用途**: 全面的测试覆盖
**触发**: Push/PR, 定时任务 (每天 02:00 UTC), 手动触发
**包含**:
- 单元测试
- 集成测试
- E2E 测试
- 性能测试 (Locust)
- 区块链集成测试

### 4. security.yml - 安全扫描
**用途**: 全面的安全检查
**触发**: Push/PR, 定时任务 (每周一 03:00 UTC), 手动触发
**包含**:
- 依赖漏洞扫描 (Safety, pip-audit)
- 代码安全扫描 (Bandit)
- 密钥泄露检测 (Gitleaks, TruffleHog)
- SAST 扫描 (CodeQL)
- Docker 镜像扫描 (Trivy, Grype)
- 基础设施扫描 (Checkov)
- 许可证合规检查
- API 安全扫描 (OWASP ZAP)

### 5. ci-cd.yml (旧版)
**状态**: 已被 ci.yml 和 cd.yml 替代
**建议**: 可以删除或保留作为参考

## 工作流依赖关系

```
代码提交
  ↓
CI (ci.yml) ────────→ 代码检查 + 测试
  ↓
CD (cd.yml) ────────→ 构建 + 部署
  ↓
Test (test.yml) ────→ 全面测试 (定时)
  ↓
Security (security.yml) → 安全扫描 (定时)
```

## 配置要求

### GitHub Secrets
参考 [CICD_SETUP_GUIDE.md](../../CICD_SETUP_GUIDE.md) 配置必需的 Secrets。

### GitHub Environments
- `staging`: 测试环境
- `production`: 生产环境 (需要审批)

## 使用指南

### 查看工作流状态
1. 进入仓库的 `Actions` 标签
2. 选择要查看的工作流
3. 查看运行历史和详细日志

### 手动触发工作流
1. 进入 `Actions` 标签
2. 选择工作流
3. 点击 `Run workflow`
4. 选择分支和参数
5. 点击 `Run workflow` 确认

### 下载报告
1. 进入工作流运行详情
2. 滚动到底部的 `Artifacts` 部分
3. 下载需要的报告

## 故障排查

### CI 失败
- 查看详细日志定位问题
- 本地运行相同命令复现
- 检查依赖版本

### CD 失败
- 检查 Secrets 配置
- 检查环境配置
- 验证部署脚本

### 测试失败
- 查看测试日志
- 检查数据库连接
- 验证环境变量

## 维护

### 定期任务
- 每周检查安全扫描报告
- 每月优化工作流性能
- 每季度更新工具版本

### 更新工作流
1. 编辑 `.github/workflows/*.yml` 文件
2. 提交并推送更改
3. 验证工作流运行正常

## 文档

- [CI/CD 配置指南](../../CICD_SETUP_GUIDE.md)
- [CI/CD 最佳实践](../../CICD_BEST_PRACTICES.md)
- [CI/CD 实施报告](../../CICD_IMPLEMENTATION_REPORT.md)
- [CI/CD 快速参考](../../CICD_QUICK_REFERENCE.md)

## 支持

如有问题，请：
1. 查看工作流日志
2. 参考文档
3. 提交 Issue
4. 联系 DevOps 团队
