# CI/CD 最佳实践

## 概述

本文档总结了 Nautilus 项目 CI/CD 流程的最佳实践，帮助团队构建高效、可靠、安全的持续集成和持续部署流程。

## 工作流设计原则

### 1. 快速反馈原则

**目标**: 在 10 分钟内完成 CI 流程

#### 实践方法
- **并行执行**: 独立任务并行运行
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
  test:
    runs-on: ubuntu-latest
  build:
    runs-on: ubuntu-latest
# lint, test, build 并行执行
```

- **增量测试**: 只运行受影响的测试
```yaml
- name: Run affected tests
  run: |
    git diff --name-only origin/main | grep "\.py$" | \
    xargs pytest --testmon
```

- **智能缓存**: 缓存依赖和构建产物
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

### 2. 失败快速原则

**目标**: 尽早发现问题，减少资源浪费

#### 实践方法
- **关键检查优先**: 先运行快速检查
```yaml
jobs:
  quick-checks:
    steps:
      - name: Syntax check
      - name: Import check
      - name: Lint

  full-tests:
    needs: quick-checks  # 只有快速检查通过才运行完整测试
```

- **设置失败阈值**: 达到阈值立即停止
```yaml
pytest --maxfail=5  # 5 个测试失败后停止
```

- **超时保护**: 防止任务无限运行
```yaml
jobs:
  test:
    timeout-minutes: 30
    steps:
      - run: pytest --timeout=300
```

### 3. 可重复性原则

**目标**: 任何时候运行都得到相同结果

#### 实践方法
- **固定依赖版本**
```txt
# requirements.txt
fastapi==0.104.1  # 使用精确版本
uvicorn==0.24.0
```

- **使用容器化环境**
```yaml
jobs:
  test:
    container:
      image: python:3.13-slim
```

- **隔离测试环境**
```yaml
services:
  postgres:
    image: postgres:15  # 固定版本
```

### 4. 可观测性原则

**目标**: 清晰了解流程状态和问题

#### 实践方法
- **详细日志**
```yaml
- name: Run tests
  run: pytest -v --tb=short --log-cli-level=INFO
```

- **生成报告**
```yaml
- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: htmlcov/
```

- **状态摘要**
```yaml
- name: Generate summary
  run: |
    echo "## Test Results" >> $GITHUB_STEP_SUMMARY
    echo "✅ Passed: 150" >> $GITHUB_STEP_SUMMARY
    echo "❌ Failed: 2" >> $GITHUB_STEP_SUMMARY
```

### 5. 安全第一原则

**目标**: 保护代码、数据和基础设施安全

#### 实践方法
- **使用 Secrets 管理敏感信息**
```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  # 永远不要硬编码密钥
```

- **最小权限原则**
```yaml
permissions:
  contents: read
  packages: write
  # 只授予必要权限
```

- **定期安全扫描**
```yaml
- name: Security scan
  run: |
    bandit -r .
    safety check
    trivy image myapp:latest
```

## 代码质量最佳实践

### 1. 代码格式化

**自动化格式化，避免人工争议**

```yaml
- name: Format check
  run: |
    black --check .
    isort --check-only .
```

**本地配置**
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py313']

[tool.isort]
profile = "black"
line_length = 100
```

### 2. 静态分析

**多层次检查**

```yaml
# 语法错误（必须通过）
- run: flake8 . --select=E9,F63,F7,F82

# 代码质量（警告）
- run: pylint api/ --fail-under=8.0 || true

# 类型检查（警告）
- run: mypy . --ignore-missing-imports || true
```

### 3. 测试策略

**测试金字塔**
```
        /\
       /E2E\      10% - 端到端测试
      /------\
     /  集成  \    20% - 集成测试
    /----------\
   /   单元测试  \  70% - 单元测试
  /--------------\
```

**测试标记**
```python
# tests/conftest.py
import pytest

@pytest.mark.unit
def test_function():
    pass

@pytest.mark.integration
def test_api():
    pass

@pytest.mark.slow
def test_performance():
    pass
```

**分层运行**
```yaml
# 快速测试（每次提交）
- run: pytest -m "unit" --maxfail=5

# 完整测试（PR 合并前）
- run: pytest -m "unit or integration"

# 全面测试（定时任务）
- run: pytest
```

### 4. 代码覆盖率

**合理的覆盖率目标**
- 单元测试: ≥ 85%
- 集成测试: ≥ 70%
- 总体覆盖率: ≥ 80%

```yaml
- name: Check coverage
  run: |
    pytest --cov=api --cov=models --cov=utils \
      --cov-report=term-missing \
      --cov-fail-under=80
```

**排除不必要的文件**
```ini
# .coveragerc
[run]
omit =
    tests/*
    */migrations/*
    */venv/*
    */__pycache__/*
```

## 部署最佳实践

### 1. 环境隔离

**多环境策略**
```
开发环境 (dev)     → 自动部署，每次提交
测试环境 (staging) → 自动部署，main 分支
生产环境 (prod)    → 手动审批，版本标签
```

**环境配置**
```yaml
# staging
environment:
  name: staging
  url: https://staging.example.com

# production
environment:
  name: production
  url: https://example.com
  # 需要审批
```

### 2. 蓝绿部署

**零停机部署**
```yaml
- name: Deploy new version (green)
  run: |
    kubectl apply -f deployment-green.yaml
    kubectl wait --for=condition=ready pod -l version=green

- name: Switch traffic
  run: |
    kubectl patch service myapp -p '{"spec":{"selector":{"version":"green"}}}'

- name: Remove old version (blue)
  run: |
    kubectl delete deployment myapp-blue
```

### 3. 金丝雀发布

**渐进式发布**
```yaml
- name: Deploy canary (10%)
  run: |
    kubectl set image deployment/myapp-canary myapp=myapp:new
    kubectl scale deployment/myapp-canary --replicas=1

- name: Monitor metrics
  run: |
    # 监控错误率、延迟等指标
    ./monitor-canary.sh

- name: Full rollout
  if: success()
  run: |
    kubectl set image deployment/myapp myapp=myapp:new
```

### 4. 回滚策略

**快速回滚机制**
```yaml
- name: Deploy with rollback
  run: |
    kubectl apply -f deployment.yaml --record
    kubectl rollout status deployment/myapp

- name: Rollback on failure
  if: failure()
  run: |
    kubectl rollout undo deployment/myapp
    kubectl rollout status deployment/myapp
```

**保留历史版本**
```yaml
spec:
  revisionHistoryLimit: 10  # 保留 10 个历史版本
```

## 安全最佳实践

### 1. Secrets 管理

**分层管理**
```
GitHub Secrets (敏感)
  ↓
Environment Variables (配置)
  ↓
Application Config (公开)
```

**Secrets 命名规范**
```
AWS_ACCESS_KEY_ID          # 云服务凭证
DB_PASSWORD                # 数据库密码
API_KEY_PRODUCTION         # 生产环境 API 密钥
API_KEY_STAGING            # 测试环境 API 密钥
SLACK_WEBHOOK_URL          # 通知 webhook
```

**使用示例**
```yaml
env:
  DATABASE_URL: postgresql://${{ secrets.DB_USER }}:${{ secrets.DB_PASSWORD }}@host/db
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
```

### 2. 依赖安全

**自动化依赖更新**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

**安全扫描**
```yaml
- name: Scan dependencies
  run: |
    safety check --json
    pip-audit --requirement requirements.txt
```

**锁定依赖版本**
```bash
# 生成精确版本
pip freeze > requirements.txt

# 或使用 pip-tools
pip-compile requirements.in
```

### 3. 容器安全

**最小化镜像**
```dockerfile
# 使用 slim 或 alpine 基础镜像
FROM python:3.13-slim

# 多阶段构建
FROM python:3.13 as builder
RUN pip install --user -r requirements.txt

FROM python:3.13-slim
COPY --from=builder /root/.local /root/.local
```

**非 root 用户**
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

**镜像扫描**
```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:latest
    severity: 'CRITICAL,HIGH'
```

### 4. 代码安全

**静态分析**
```yaml
- name: Security scan
  run: |
    bandit -r . -f json -o bandit-report.json
```

**密钥检测**
```yaml
- name: Detect secrets
  uses: gitleaks/gitleaks-action@v2
```

**SAST 扫描**
```yaml
- name: CodeQL Analysis
  uses: github/codeql-action/analyze@v3
```

## 性能优化实践

### 1. 构建优化

**Docker 层缓存**
```dockerfile
# 先复制依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 后复制代码（代码变更不影响依赖层）
COPY . .
```

**GitHub Actions 缓存**
```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      ~/.cache/pre-commit
    key: ${{ runner.os }}-${{ hashFiles('**/requirements.txt') }}
```

### 2. 测试优化

**并行测试**
```yaml
- name: Run tests in parallel
  run: pytest -n auto  # 使用所有 CPU 核心
```

**测试分片**
```yaml
strategy:
  matrix:
    shard: [1, 2, 3, 4]
steps:
  - run: pytest --shard-id=${{ matrix.shard }} --num-shards=4
```

### 3. 部署优化

**预热容器**
```yaml
- name: Warm up
  run: |
    curl http://localhost:8000/health
    curl http://localhost:8000/api/v1/agents
```

**健康检查**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 监控和告警实践

### 1. 工作流监控

**状态徽章**
```markdown
![CI](https://github.com/org/repo/workflows/CI/badge.svg)
![CD](https://github.com/org/repo/workflows/CD/badge.svg)
```

**失败通知**
```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'CI Pipeline failed!'
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 2. 部署监控

**部署指标**
```yaml
- name: Record deployment
  run: |
    curl -X POST https://metrics.example.com/deployments \
      -d "version=${{ github.sha }}" \
      -d "environment=production" \
      -d "timestamp=$(date -u +%s)"
```

**健康检查**
```yaml
- name: Health check
  run: |
    for i in {1..10}; do
      if curl -f https://example.com/health; then
        echo "✅ Health check passed"
        exit 0
      fi
      sleep 10
    done
    echo "❌ Health check failed"
    exit 1
```

### 3. 错误追踪

**集成错误追踪服务**
```yaml
- name: Report to Sentry
  if: failure()
  run: |
    curl -X POST https://sentry.io/api/0/projects/org/project/events/ \
      -H "Authorization: Bearer ${{ secrets.SENTRY_TOKEN }}" \
      -d "message=CI Pipeline failed"
```

## 团队协作实践

### 1. 分支策略

**Git Flow**
```
main (生产)
  ↑
develop (开发)
  ↑
feature/* (功能)
hotfix/* (紧急修复)
```

**工作流配置**
```yaml
on:
  push:
    branches:
      - main
      - develop
      - 'feature/**'
      - 'hotfix/**'
```

### 2. PR 流程

**PR 模板**
```markdown
## 变更描述
<!-- 描述本次变更的内容 -->

## 变更类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 重构
- [ ] 文档更新

## 测试
- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 手动测试已完成

## 检查清单
- [ ] 代码已格式化
- [ ] 文档已更新
- [ ] 无安全问题
```

**自动检查**
```yaml
- name: PR checks
  run: |
    # 检查 PR 标题格式
    # 检查是否有冲突
    # 检查是否有 TODO
```

### 3. Code Review

**自动化 Review**
```yaml
- name: Auto review
  uses: reviewdog/action-reviewdog@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    reporter: github-pr-review
```

**Review 要求**
```yaml
# .github/CODEOWNERS
# 自动分配 reviewer
*.py @backend-team
*.yml @devops-team
```

## 故障处理实践

### 1. 快速诊断

**详细日志**
```yaml
- name: Debug info
  if: failure()
  run: |
    echo "=== Environment ==="
    env | sort
    echo "=== Disk usage ==="
    df -h
    echo "=== Memory ==="
    free -h
    echo "=== Processes ==="
    ps aux
```

### 2. 自动恢复

**重试机制**
```yaml
- name: Deploy with retry
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    command: ./deploy.sh
```

### 3. 降级策略

**功能开关**
```python
# 使用环境变量控制功能
ENABLE_NEW_FEATURE = os.getenv("ENABLE_NEW_FEATURE", "false") == "true"

if ENABLE_NEW_FEATURE:
    # 新功能代码
else:
    # 旧功能代码
```

## 成本优化实践

### 1. 减少运行时间

**条件执行**
```yaml
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.github/**'
```

**跳过重复构建**
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### 2. 资源优化

**使用合适的 Runner**
```yaml
jobs:
  small-job:
    runs-on: ubuntu-latest  # 标准 runner

  large-job:
    runs-on: ubuntu-latest-4-cores  # 大型 runner
```

### 3. 自托管 Runner

**适用场景**
- 频繁运行的工作流
- 需要特殊硬件/软件
- 需要访问内部资源

```yaml
jobs:
  build:
    runs-on: self-hosted
```

## 文档和知识管理

### 1. 文档即代码

**工作流文档**
```yaml
name: CI Pipeline
# 这个工作流负责：
# 1. 代码质量检查
# 2. 运行测试
# 3. 构建 Docker 镜像
```

### 2. Runbook

**创建操作手册**
```markdown
# 部署失败处理

## 症状
部署到生产环境失败

## 诊断步骤
1. 检查工作流日志
2. 检查应用日志
3. 检查基础设施状态

## 解决方案
1. 回滚到上一版本
2. 修复问题
3. 重新部署
```

### 3. 变更日志

**自动生成**
```yaml
- name: Generate changelog
  run: |
    git log --oneline $(git describe --tags --abbrev=0)..HEAD > CHANGELOG.md
```

## 总结

### 核心原则
1. **自动化优先**: 能自动化的都自动化
2. **快速反馈**: 尽早发现问题
3. **安全第一**: 保护代码和数据
4. **持续改进**: 定期回顾和优化

### 关键指标
- **构建时间**: < 10 分钟
- **测试覆盖率**: ≥ 80%
- **部署频率**: 每天多次
- **失败恢复时间**: < 1 小时
- **变更失败率**: < 15%

### 持续改进
- 定期回顾工作流性能
- 收集团队反馈
- 学习行业最佳实践
- 更新工具和流程
