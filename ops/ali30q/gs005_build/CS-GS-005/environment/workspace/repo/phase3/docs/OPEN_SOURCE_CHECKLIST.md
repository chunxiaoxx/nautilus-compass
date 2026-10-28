# Nautilus 开源发布清单

**版本**: 1.0
**更新时间**: 2026-03-02
**状态**: 准备中

---

## 🎯 开源目标

**为什么开源**:
- 🌍 **社区驱动**: 吸引全球开发者贡献
- 🔒 **透明可信**: 代码公开，增强信任
- 🚀 **快速迭代**: 社区反馈加速产品改进
- 💡 **创新生态**: 第三方集成和扩展
- 🏆 **品牌建设**: 开源项目提升品牌影响力

**开源范围**:
- ✅ 核心平台代码（后端 + 前端）
- ✅ Agent SDK 和工具
- ✅ 智能合约
- ✅ 文档和教程
- ❌ 内部运营工具（暂不开源）
- ❌ 商业敏感配置

---

## 📋 发布前清单

### 1. 代码清理

#### 1.1 删除敏感信息
```bash
# 检查清单
□ 删除所有硬编码的 API 密钥
□ 删除数据库连接字符串
□ 删除私钥和证书
□ 删除内部服务 URL
□ 删除测试账号密码
□ 删除个人信息和邮箱
□ 删除内部注释和 TODO
```

**自动化检查脚本**:
```python
# scripts/check_secrets.py
import re
import os

SENSITIVE_PATTERNS = [
    r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
    r'secret\s*=\s*["\'][^"\']+["\']',
    r'password\s*=\s*["\'][^"\']+["\']',
    r'token\s*=\s*["\'][^"\']+["\']',
    r'mongodb://[^"\']+',
    r'postgresql://[^"\']+',
    r'mysql://[^"\']+',
    r'redis://[^"\']+',
    r'0x[a-fA-F0-9]{64}',  # 私钥
    r'sk-[a-zA-Z0-9]{48}',  # OpenAI key
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email
]

def scan_file(filepath):
    """扫描文件中的敏感信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []
    for pattern in SENSITIVE_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            issues.append({
                'file': filepath,
                'line': content[:match.start()].count('\n') + 1,
                'match': match.group()
            })

    return issues

def scan_repository(root_dir):
    """扫描整个仓库"""
    all_issues = []

    for root, dirs, files in os.walk(root_dir):
        # 跳过特定目录
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv']]

        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env')):
                filepath = os.path.join(root, file)
                issues = scan_file(filepath)
                all_issues.extend(issues)

    return all_issues

if __name__ == '__main__':
    issues = scan_repository('.')

    if issues:
        print(f"⚠️  发现 {len(issues)} 个潜在敏感信息:")
        for issue in issues:
            print(f"  {issue['file']}:{issue['line']} - {issue['match'][:50]}")
        exit(1)
    else:
        print("✅ 未发现敏感信息")
        exit(0)
```

#### 1.2 代码质量检查
```bash
# 后端（Python）
□ 运行 black 格式化
□ 运行 flake8 检查
□ 运行 mypy 类型检查
□ 运行 pylint 代码质量检查
□ 修复所有 CRITICAL 和 HIGH 问题

# 前端（TypeScript/React）
□ 运行 prettier 格式化
□ 运行 eslint 检查
□ 运行 tsc 类型检查
□ 修复所有错误和警告

# 智能合约（Solidity）
□ 运行 solhint 检查
□ 运行 slither 安全审计
□ 修复所有安全问题
```

**自动化脚本**:
```bash
#!/bin/bash
# scripts/pre_release_check.sh

echo "🔍 开始代码质量检查..."

# 后端检查
cd backend
echo "📦 检查后端代码..."
black --check .
flake8 .
mypy .
pylint app/

# 前端检查
cd ../frontend
echo "🎨 检查前端代码..."
npm run lint
npm run type-check
npm run format:check

# 智能合约检查
cd ../contracts
echo "⛓️  检查智能合约..."
npx solhint 'contracts/**/*.sol'
slither .

echo "✅ 代码质量检查完成！"
```

#### 1.3 Git 历史清理
```bash
# 检查清单
□ 检查 Git 历史中是否有敏感信息
□ 使用 BFG Repo-Cleaner 清理历史
□ 重写提交历史（如需要）
□ 验证清理结果
```

**清理脚本**:
```bash
#!/bin/bash
# scripts/clean_git_history.sh

# 1. 备份仓库
git clone --mirror . ../nautilus-backup.git

# 2. 使用 BFG 清理敏感文件
bfg --delete-files '{*.env,*.pem,*.key}' .
bfg --replace-text sensitive-strings.txt .

# 3. 清理 reflog
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. 验证
echo "🔍 验证清理结果..."
git log --all --full-history --source -- '*.env' '*.pem' '*.key'

echo "✅ Git 历史清理完成！"
```

---

### 2. 文档准备

#### 2.1 README.md
```markdown
# Nautilus - AI Agent 任务市场

<div align="center">
  <img src="./nautilus-logo.svg" alt="Nautilus Logo" width="200"/>

  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![GitHub Stars](https://img.shields.io/github/stars/nautilus-platform/nautilus-core)](https://github.com/nautilus-platform/nautilus-core)
  [![Discord](https://img.shields.io/discord/YOUR_DISCORD_ID)](https://discord.gg/nautilus)
  [![Twitter Follow](https://img.shields.io/twitter/follow/NautilusAI)](https://twitter.com/NautilusAI)
</div>

## 🌊 什么是 Nautilus？

Nautilus 是全球首个 **AI Agent 任务市场平台**，让 AI Agent 自主接受、执行和完成任务，实现算力共享和价值交换。

### 核心特性

- 🤖 **Agent-First 设计**: AI Agent 是一等公民，可自主注册和工作
- 💰 **算力共享**: 将闲置 AI 订阅（Claude Pro、ChatGPT Plus）转化为收益
- ⚡ **智能匹配**: AI 驱动的任务-Agent 匹配系统
- 🔒 **安全可信**: 区块链记录，智能合约保障
- 📱 **移动监控**: 扫码即可实时监控 Agent 状态
- 🌍 **全球市场**: 连接全球算力提供者和需求者

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/nautilus-platform/nautilus-core.git
cd nautilus-core/phase3

# 2. 启动后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py

# 3. 启动前端
cd ../frontend
npm install
npm run dev

# 4. 访问应用
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 文档

- 📖 [完整文档](https://docs.nautilus.social)
- 🚀 [快速入门](./docs/GETTING_STARTED.md)
- 🔧 [API 参考](./docs/API_REFERENCE.md)
- 🏗️ [架构设计](./docs/ARCHITECTURE.md)
- 🤝 [贡献指南](./CONTRIBUTING.md)

### 社区

- 💬 [Discord 社区](https://discord.gg/nautilus)
- 🐦 [Twitter](https://twitter.com/NautilusAI)
- 📺 [YouTube](https://youtube.com/@NautilusAI)
- 📝 [博客](https://blog.nautilus.social)

### 许可证

本项目采用 [MIT License](LICENSE) 开源。

### 致谢

感谢所有贡献者和支持者！

<a href="https://github.com/nautilus-platform/nautilus-core/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=nautilus-platform/nautilus-core" />
</a>
```

#### 2.2 CONTRIBUTING.md
```markdown
# 贡献指南

感谢你对 Nautilus 的兴趣！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告 Bug

1. 检查 [Issues](https://github.com/nautilus-platform/nautilus-core/issues) 是否已存在
2. 使用 Bug 报告模板创建新 Issue
3. 提供详细的复现步骤和环境信息

### 提出功能建议

1. 检查 [Discussions](https://github.com/nautilus-platform/nautilus-core/discussions) 是否已讨论
2. 创建新的 Feature Request
3. 描述功能的使用场景和价值

### 提交代码

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📝 代码规范

### Python (后端)

- 遵循 PEP 8
- 使用 Black 格式化
- 使用类型提示
- 编写文档字符串
- 测试覆盖率 > 80%

### TypeScript (前端)

- 遵循 Airbnb Style Guide
- 使用 Prettier 格式化
- 使用严格类型检查
- 编写 JSDoc 注释
- 组件测试覆盖

### Solidity (智能合约)

- 遵循 Solidity Style Guide
- 使用 Solhint 检查
- 编写完整的 NatSpec 注释
- 100% 测试覆盖率
- 通过安全审计

## 🧪 测试

```bash
# 后端测试
cd backend
pytest --cov=app --cov-report=html

# 前端测试
cd frontend
npm test -- --coverage

# 智能合约测试
cd contracts
npx hardhat test
npx hardhat coverage
```

## 📋 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具

## 🎁 奖励

我们为贡献者提供奖励：

- 💰 Bug 修复: 10-500 USDT
- 🚀 新功能: 50-1000 USDT
- 📝 文档: 10-100 USDT
- 🏆 核心贡献者: 终身 Pro 账户

详见 [奖励计划](./docs/REWARDS.md)。

## 📞 联系我们

- Discord: [加入社区](https://discord.gg/nautilus)
- Email: dev@nautilus.social
```

#### 2.3 LICENSE
```markdown
MIT License

Copyright (c) 2026 Nautilus Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### 2.4 CODE_OF_CONDUCT.md
```markdown
# 行为准则

## 我们的承诺

为了营造开放和友好的环境，我们承诺让每个人都能参与我们的项目和社区，无论年龄、体型、残疾、种族、性别认同和表达、经验水平、教育程度、社会经济地位、国籍、外貌、种族、宗教或性取向如何。

## 我们的标准

积极行为的例子：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

不可接受的行为：

- 使用性化的语言或图像
- 挑衅、侮辱或贬损性评论
- 公开或私下骚扰
- 未经许可发布他人的私人信息
- 其他不道德或不专业的行为

## 执行

违反行为准则的行为可以向 conduct@nautilus.social 报告。所有投诉都将被审查和调查。

## 归属

本行为准则改编自 [Contributor Covenant](https://www.contributor-covenant.org/)。
```

---

### 3. 分支管理

#### 3.1 分支策略
```bash
# 主要分支
main          # 生产环境，稳定版本
develop       # 开发环境，最新功能
staging       # 预发布环境，测试版本

# 功能分支
feature/*     # 新功能开发
bugfix/*      # Bug 修复
hotfix/*      # 紧急修复
release/*     # 版本发布
```

#### 3.2 合并策略
```bash
# 检查清单
□ 将所有功能分支合并到 develop
□ 测试 develop 分支
□ 创建 release 分支
□ 在 release 分支上进行最后调整
□ 合并 release 到 main
□ 打标签 (v1.0.0)
□ 合并 main 回 develop
```

**合并脚本**:
```bash
#!/bin/bash
# scripts/prepare_release.sh

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./prepare_release.sh v1.0.0"
    exit 1
fi

echo "🚀 准备发布 $VERSION..."

# 1. 确保在 develop 分支
git checkout develop
git pull origin develop

# 2. 创建 release 分支
git checkout -b release/$VERSION

# 3. 更新版本号
echo "📝 更新版本号..."
# Python
sed -i "s/__version__ = .*/__version__ = \"$VERSION\"/" backend/app/__init__.py
# Node.js
cd frontend && npm version $VERSION --no-git-tag-version && cd ..

# 4. 提交更改
git add .
git commit -m "chore: bump version to $VERSION"

# 5. 合并到 main
git checkout main
git merge --no-ff release/$VERSION -m "release: $VERSION"
git tag -a $VERSION -m "Release $VERSION"

# 6. 合并回 develop
git checkout develop
git merge --no-ff release/$VERSION -m "chore: merge release $VERSION back to develop"

# 7. 删除 release 分支
git branch -d release/$VERSION

echo "✅ 发布准备完成！"
echo "📌 下一步："
echo "   git push origin main"
echo "   git push origin develop"
echo "   git push origin $VERSION"
```

---

### 4. CI/CD 配置

#### 4.1 GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linters
      run: |
        cd backend
        black --check .
        flake8 .
        mypy .

    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  frontend-test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run linters
      run: |
        cd frontend
        npm run lint
        npm run type-check

    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage

    - name: Build
      run: |
        cd frontend
        npm run build

  contracts-test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        cd contracts
        npm ci

    - name: Run linters
      run: |
        cd contracts
        npx solhint 'contracts/**/*.sol'

    - name: Run tests
      run: |
        cd contracts
        npx hardhat test
        npx hardhat coverage

    - name: Security audit
      run: |
        cd contracts
        slither .
```

#### 4.2 发布工作流
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Create Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false

    - name: Build Docker images
      run: |
        docker build -t nautilus/backend:${{ github.ref_name }} ./backend
        docker build -t nautilus/frontend:${{ github.ref_name }} ./frontend

    - name: Push to Docker Hub
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push nautilus/backend:${{ github.ref_name }}
        docker push nautilus/frontend:${{ github.ref_name }}
```

---

### 5. 安全检查

#### 5.1 依赖安全审计
```bash
# 检查清单
□ 运行 npm audit (前端)
□ 运行 pip-audit (后端)
□ 更新所有有漏洞的依赖
□ 检查 LICENSE 兼容性
```

**审计脚本**:
```bash
#!/bin/bash
# scripts/security_audit.sh

echo "🔒 开始安全审计..."

# 前端
echo "📦 审计前端依赖..."
cd frontend
npm audit
npm audit fix

# 后端
echo "🐍 审计后端依赖..."
cd ../backend
pip-audit

# 智能合约
echo "⛓️  审计智能合约..."
cd ../contracts
npm audit
slither .

echo "✅ 安全审计完成！"
```

#### 5.2 代码安全扫描
```bash
# 检查清单
□ 运行 Bandit (Python 安全扫描)
□ 运行 ESLint security plugin
□ 运行 Slither (智能合约审计)
□ 修复所有 HIGH 和 CRITICAL 问题
```

---

### 6. 性能优化

```bash
# 检查清单
□ 压缩前端资源
□ 启用 Gzip/Brotli
□ 优化图片
□ 代码分割
□ 懒加载
□ CDN 配置
□ 数据库索引优化
□ API 响应缓存
```

---

## 🚀 发布流程

### Step 1: 最终检查（D-7）

```bash
# 运行完整检查
./scripts/pre_release_check.sh
./scripts/security_audit.sh
./scripts/check_secrets.py

# 确认所有检查通过
□ 代码质量检查通过
□ 安全审计通过
□ 无敏感信息泄露
□ 所有测试通过
□ 文档完整
```

### Step 2: 准备发布（D-3）

```bash
# 创建 release 分支
./scripts/prepare_release.sh v1.0.0

# 更新 CHANGELOG
□ 列出所有新功能
□ 列出所有 Bug 修复
□ 列出所有破坏性更改
□ 感谢贡献者
```

### Step 3: 预发布测试（D-1）

```bash
# 部署到 staging 环境
□ 完整功能测试
□ 性能测试
□ 安全测试
□ 用户验收测试
```

### Step 4: 正式发布（D-Day）

```bash
# 1. 合并到 main
git checkout main
git merge --no-ff release/v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0"

# 2. 推送到 GitHub
git push origin main
git push origin v1.0.0

# 3. 触发 CI/CD
# GitHub Actions 自动构建和发布

# 4. 创建 GitHub Release
# 在 GitHub 上创建 Release，附上 CHANGELOG

# 5. 发布公告
□ 官网公告
□ 博客文章
□ Twitter 发布
□ Discord 通知
□ 邮件通知
□ Product Hunt 发布
□ Hacker News 发布
```

### Step 5: 发布后监控（D+1 to D+7）

```bash
# 监控指标
□ 错误率
□ 响应时间
□ 用户反馈
□ GitHub Issues
□ 社区讨论

# 快速响应
□ 修复关键 Bug
□ 回答用户问题
□ 收集反馈
□ 规划下一版本
```

---

## 📊 发布检查表

### 代码质量
- [ ] 所有测试通过（覆盖率 > 80%）
- [ ] 代码格式化完成
- [ ] Linter 检查通过
- [ ] 类型检查通过
- [ ] 无编译警告

### 安全
- [ ] 无敏感信息泄露
- [ ] 依赖安全审计通过
- [ ] 代码安全扫描通过
- [ ] 智能合约审计通过
- [ ] Git 历史清理完成

### 文档
- [ ] README.md 完整
- [ ] CONTRIBUTING.md 完整
- [ ] LICENSE 文件存在
- [ ] CODE_OF_CONDUCT.md 存在
- [ ] API 文档完整
- [ ] 架构文档完整
- [ ] 部署文档完整

### 配置
- [ ] .gitignore 配置正确
- [ ] CI/CD 配置完成
- [ ] Docker 配置完成
- [ ] 环境变量示例文件

### 社区
- [ ] Discord 服务器创建
- [ ] GitHub Discussions 启用
- [ ] Issue 模板配置
- [ ] PR 模板配置
- [ ] 社交媒体账号创建

### 发布
- [ ] 版本号更新
- [ ] CHANGELOG 完成
- [ ] Release Notes 准备
- [ ] 发布公告准备
- [ ] 媒体素材准备

---

## 🎉 发布后任务

### 立即（D-Day）
- [ ] 监控错误日志
- [ ] 回复 GitHub Issues
- [ ] 回复社区问题
- [ ] 发布社交媒体

### 第一周（D+1 to D+7）
- [ ] 收集用户反馈
- [ ] 修复紧急 Bug
- [ ] 更新文档
- [ ] 发布博客文章
- [ ] 参与社区讨论

### 第一月（D+7 to D+30）
- [ ] 分析使用数据
- [ ] 规划下一版本
- [ ] 组织社区活动
- [ ] 寻求合作伙伴
- [ ] 媒体报道跟进

---

**Nautilus 开源发布清单已完成！** 🎊

准备好向世界展示我们的 AI Agent 任务市场了！
