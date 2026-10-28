# CI/CD 快速参考

## 工作流概览

| 工作流 | 文件 | 触发条件 | 运行时间 |
|--------|------|---------|---------|
| CI | ci.yml | Push/PR | 8-12 分钟 |
| CD | cd.yml | Push main/Tag | 15-20 分钟 |
| Test | test.yml | Push/PR/定时 | 15-25 分钟 |
| Security | security.yml | Push/PR/定时 | 20-30 分钟 |

## 快速命令

### 本地测试
```bash
# 代码格式化
black .
isort .

# 代码检查
flake8 .
pylint api/ models/ utils/
mypy .

# 运行测试
pytest tests/ -v
pytest tests/ --cov=api --cov=models --cov=utils

# 安全扫描
bandit -r .
safety check
```

### Git 工作流
```bash
# 功能开发
git checkout -b feature/my-feature
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# 发布版本
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## 必需的 Secrets

### 部署相关
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
```

### 区块链测试 (可选)
```
SEPOLIA_RPC_URL
INFURA_PROJECT_ID
TEST_PRIVATE_KEY
TASK_MARKET_ADDRESS
REWARD_POOL_ADDRESS
AGENT_REGISTRY_ADDRESS
```

## 环境配置

### Staging
- 名称: `staging`
- URL: https://staging.nautilus.example.com
- 审批: 不需要

### Production
- 名称: `production`
- URL: https://nautilus.example.com
- 审批: 需要 (至少 1 人)

## 常见问题

### CI 失败
```bash
# 查看日志
Actions > 选择运行 > 查看详细日志

# 本地复现
pytest tests/ -v
```

### 部署失败
```bash
# 检查 Secrets 配置
Settings > Secrets and variables > Actions

# 检查环境配置
Settings > Environments
```

### 手动触发
```
Actions > 选择工作流 > Run workflow
```

## 关键指标

- **CI 成功率**: ≥ 95%
- **测试覆盖率**: ≥ 80%
- **部署频率**: 每天 1-5 次
- **部署成功率**: ≥ 98%

## 文档链接

- [配置指南](./CICD_SETUP_GUIDE.md)
- [最佳实践](./CICD_BEST_PRACTICES.md)
- [实施报告](./CICD_IMPLEMENTATION_REPORT.md)

## 支持

- 查看工作流日志
- 参考文档
- 提交 Issue
- 联系 DevOps 团队
