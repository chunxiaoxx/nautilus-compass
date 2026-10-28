# CI/CD 配置指南

## 概述

本文档提供了 Nautilus 后端项目的 GitHub Actions CI/CD 配置完整指南。

## 工作流概览

### 1. CI 工作流 (ci.yml)
- **触发条件**: Push 到 main/develop/feature 分支，PR 到 main/develop
- **主要任务**:
  - 代码质量检查（Black, isort, Flake8, Pylint, Mypy）
  - 依赖安全检查（Safety, pip-audit）
  - 单元测试（覆盖率 ≥ 80%）
  - 集成测试
  - Docker 镜像构建验证

### 2. CD 工作流 (cd.yml)
- **触发条件**: Push 到 main 分支，版本标签，手动触发
- **主要任务**:
  - 构建并推送 Docker 镜像到容器仓库
  - 部署到 Staging 环境
  - 部署到 Production 环境（需要审批）
  - 自动回滚机制

### 3. Test 工作流 (test.yml)
- **触发条件**: Push, PR, 定时任务（每天凌晨2点），手动触发
- **主要任务**:
  - 单元测试
  - 集成测试
  - E2E 测试
  - 性能测试
  - 区块链集成测试

### 4. Security 工作流 (security.yml)
- **触发条件**: Push, PR, 定时任务（每周一凌晨3点），手动触发
- **主要任务**:
  - 依赖漏洞扫描
  - 代码安全扫描（Bandit）
  - 密钥泄露检测（Gitleaks, TruffleHog）
  - SAST 扫描（CodeQL）
  - Docker 镜像扫描（Trivy, Grype）
  - API 安全扫描（OWASP ZAP）

## GitHub Secrets 配置

### 必需的 Secrets

#### AWS 部署相关
```
AWS_ACCESS_KEY_ID          # AWS 访问密钥 ID
AWS_SECRET_ACCESS_KEY      # AWS 访问密钥
AWS_REGION                 # AWS 区域（如 us-east-1）
```

#### 区块链测试相关
```
SEPOLIA_RPC_URL           # Sepolia 测试网 RPC URL
INFURA_PROJECT_ID         # Infura 项目 ID
TEST_PRIVATE_KEY          # 测试账户私钥（仅用于测试网）
TASK_MARKET_ADDRESS       # TaskMarket 合约地址
REWARD_POOL_ADDRESS       # RewardPool 合约地址
AGENT_REGISTRY_ADDRESS    # AgentRegistry 合约地址
```

#### 容器仓库相关
```
GITHUB_TOKEN              # 自动提供，用于 GHCR
# 或使用其他容器仓库
DOCKER_USERNAME           # Docker Hub 用户名
DOCKER_PASSWORD           # Docker Hub 密码
```

#### 可选 Secrets
```
CODECOV_TOKEN             # Codecov 上传令牌
SLACK_WEBHOOK_URL         # Slack 通知 webhook
GITLEAKS_LICENSE          # Gitleaks 许可证（企业版）
```

### 配置 Secrets 步骤

1. 进入 GitHub 仓库
2. 点击 `Settings` > `Secrets and variables` > `Actions`
3. 点击 `New repository secret`
4. 输入 Secret 名称和值
5. 点击 `Add secret`

## 环境配置

### Staging 环境

1. 进入 `Settings` > `Environments`
2. 创建 `staging` 环境
3. 配置环境变量:
   - `ENVIRONMENT=staging`
   - `API_URL=https://staging.nautilus.example.com`
4. 可选：配置部署保护规则

### Production 环境

1. 创建 `production` 环境
2. 配置环境变量:
   - `ENVIRONMENT=production`
   - `API_URL=https://nautilus.example.com`
3. **必须配置**部署保护规则:
   - 启用 `Required reviewers`（至少 1 人审批）
   - 启用 `Wait timer`（可选，等待时间如 5 分钟）

## 工作流触发条件

### 自动触发

| 工作流 | 触发事件 | 分支 |
|--------|---------|------|
| CI | Push, PR | main, develop, feature/** |
| CD | Push | main |
| CD | Tag | v*.*.* |
| Test | Push, PR | main, develop, feature/** |
| Test | Schedule | 每天 02:00 UTC |
| Security | Push, PR | main, develop |
| Security | Schedule | 每周一 03:00 UTC |

### 手动触发

所有工作流都支持手动触发（workflow_dispatch）：

1. 进入 `Actions` 标签
2. 选择要运行的工作流
3. 点击 `Run workflow`
4. 选择分支和参数
5. 点击 `Run workflow` 确认

## 工作流配置详解

### CI 工作流配置

#### 代码质量检查
```yaml
- name: Run Black (Code Formatting)
  run: black --check --diff .

- name: Run Flake8 (Linting)
  run: flake8 . --count --max-line-length=127
```

#### 测试配置
```yaml
- name: Run unit tests with coverage
  run: |
    pytest tests/ \
      --cov=api --cov=models --cov=utils \
      --cov-report=xml \
      --cov-fail-under=80
```

### CD 工作流配置

#### Docker 镜像构建
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

#### 部署到 Staging
```yaml
- name: Deploy to ECS/Kubernetes (Staging)
  run: |
    # 使用 kubectl 或 AWS CLI 部署
    kubectl set image deployment/nautilus-backend \
      nautilus-backend=${{ needs.build-and-push.outputs.image-tag }}
```

### Security 工作流配置

#### 依赖扫描
```yaml
- name: Run Safety check
  run: safety check --json --output safety-report.json

- name: Run pip-audit
  run: pip-audit --requirement requirements.txt
```

#### 代码安全扫描
```yaml
- name: Run Bandit security scan
  run: |
    bandit -r . \
      --exclude ./tests,./venv \
      --skip B101,B601
```

## 自定义配置

### 修改测试覆盖率要求

编辑 `.github/workflows/ci.yml`:
```yaml
--cov-fail-under=80  # 修改为所需的覆盖率百分比
```

### 修改部署目标

编辑 `.github/workflows/cd.yml`:
```yaml
- name: Deploy to Production
  run: |
    # 替换为你的部署命令
    kubectl set image deployment/nautilus-backend ...
    # 或使用 AWS ECS
    aws ecs update-service ...
    # 或使用 Docker Compose
    docker-compose up -d
```

### 添加通知

在工作流末尾添加通知步骤:
```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## 故障排查

### 常见问题

#### 1. 测试失败
```bash
# 本地运行测试
pytest tests/ -v

# 检查数据库连接
psql -h localhost -U postgres -d nautilus_test
```

#### 2. Docker 构建失败
```bash
# 本地构建测试
docker build -t nautilus-backend:test .

# 检查 Dockerfile 语法
docker build --no-cache -t nautilus-backend:test .
```

#### 3. 部署失败
```bash
# 检查 Secrets 配置
# 确保所有必需的 Secrets 已配置

# 检查环境配置
# 确保 staging/production 环境已创建
```

#### 4. 权限问题
```bash
# 确保 GITHUB_TOKEN 有足够权限
# Settings > Actions > General > Workflow permissions
# 选择 "Read and write permissions"
```

### 调试技巧

#### 启用调试日志
在工作流中添加:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

#### 使用 tmate 进行交互式调试
```yaml
- name: Setup tmate session
  uses: mxschmitt/action-tmate@v3
  if: failure()
```

## 性能优化

### 缓存依赖
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.13'
    cache: 'pip'  # 启用 pip 缓存
```

### 并行测试
```yaml
- name: Run tests in parallel
  run: pytest tests/ -n auto  # 使用 pytest-xdist
```

### Docker 层缓存
```yaml
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## 最佳实践

### 1. 分支策略
- `main`: 生产环境代码
- `develop`: 开发环境代码
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复分支

### 2. 提交规范
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式化
refactor: 重构
test: 测试相关
chore: 构建/工具链相关
```

### 3. PR 流程
1. 创建 feature 分支
2. 提交代码并推送
3. 创建 PR 到 develop
4. CI 自动运行
5. Code Review
6. 合并到 develop
7. 定期合并 develop 到 main

### 4. 版本发布
```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 自动触发 CD 工作流部署到生产环境
```

### 5. 回滚策略
```bash
# 方式 1: 使用 kubectl
kubectl rollout undo deployment/nautilus-backend

# 方式 2: 重新部署之前的版本
kubectl set image deployment/nautilus-backend \
  nautilus-backend=ghcr.io/org/nautilus-backend:v1.0.0
```

## 监控和告警

### 工作流状态监控
- 在 GitHub Actions 页面查看工作流运行状态
- 配置 GitHub 通知接收失败告警

### 集成外部监控
```yaml
- name: Send metrics to monitoring
  run: |
    curl -X POST https://monitoring.example.com/metrics \
      -d "workflow=${{ github.workflow }}" \
      -d "status=${{ job.status }}"
```

## 安全考虑

### 1. Secrets 管理
- 永远不要在代码中硬编码密钥
- 使用 GitHub Secrets 存储敏感信息
- 定期轮换密钥

### 2. 权限最小化
- 为每个环境使用独立的凭证
- 限制 GitHub Token 权限
- 使用只读令牌进行扫描

### 3. 依赖安全
- 定期运行安全扫描
- 及时更新依赖版本
- 使用 Dependabot 自动更新

### 4. 镜像安全
- 使用官方基础镜像
- 定期扫描镜像漏洞
- 使用非 root 用户运行容器

## 成本优化

### 1. 减少工作流运行时间
- 使用缓存
- 并行运行任务
- 跳过不必要的步骤

### 2. 优化触发条件
```yaml
on:
  push:
    branches: [ main ]
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### 3. 使用自托管 Runner
对于频繁运行的工作流，考虑使用自托管 Runner 以降低成本。

## 参考资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker 最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes 部署指南](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [OWASP 安全指南](https://owasp.org/)

## 支持

如有问题，请：
1. 查看工作流运行日志
2. 参考本文档的故障排查部分
3. 提交 Issue 到项目仓库
