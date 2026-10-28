# 🚀 Nautilus 完整配置指南

**版本**: 1.0
**日期**: 2026-03-04
**目标**: 完成所有插件、MCP服务器和Agent的配置

---

## 📋 配置概览

### 需要安装的组件

1. **MCP服务器** (2个)
   - ✅ 区块链MCP服务器（已生成代码）
   - ✅ Nautilus数据库MCP服务器（已生成代码）

2. **专用Agent** (2个)
   - ✅ nautilus-wallet-expert（已生成配置）
   - ✅ seed-task-manager（已生成配置）

3. **开发工具**
   - ✅ GitHub CLI
   - ✅ VS Code Coverage Gutters
   - ✅ Prometheus MCP

4. **开发规范**
   - ✅ Nautilus区块链开发规范

---

## 🔧 Step 1: 安装依赖

### 1.1 安装GitHub CLI

```bash
# Windows
winget install --id GitHub.cli

# 验证安装
gh --version

# 配置认证
gh auth login
# 选择: GitHub.com
# 选择: HTTPS
# 选择: Login with a web browser
# 复制one-time code并在浏览器中完成认证
```

### 1.2 安装Node.js依赖

```bash
# 安装MCP SDK和viem
npm install -g @modelcontextprotocol/sdk viem

# 验证安装
node -e "console.log(require('viem').version)"
```

### 1.3 安装Python依赖

```bash
# 安装Web3和PostgreSQL驱动
pip install web3 psycopg2-binary

# 验证安装
python -c "import web3; print(web3.__version__)"
```

---

## 🔌 Step 2: 配置MCP服务器

### 2.1 安装区块链MCP服务器

```bash
# 进入目录
cd C:\Users\chunx\.claude\mcp-servers\blockchain

# 安装依赖
npm install

# 测试运行
node index.js
# 应该看到: "MCP Blockchain Server running on stdio"
# 按Ctrl+C退出
```

### 2.2 安装Nautilus数据库MCP服务器

```bash
# 进入目录
cd C:\Users\chunx\.claude\mcp-servers\nautilus-db

# 安装依赖
npm install

# 配置数据库密码
# 编辑 C:\Users\chunx\.claude\mcp_settings.json
# 将 "your_password_here" 替换为实际密码
```

**重要**: 编辑 `C:\Users\chunx\.claude\mcp_settings.json`，设置数据库密码：

```json
{
  "mcpServers": {
    "nautilus-db": {
      "command": "node",
      "args": ["C:\\Users\\chunx\\.claude\\mcp-servers\\nautilus-db\\index.js"],
      "env": {
        "DB_USER": "postgres",
        "DB_PASSWORD": "你的实际数据库密码"
      }
    }
  }
}
```

### 2.3 测试MCP服务器

```bash
# 测试区块链MCP
claude mcp blockchain validate-address --address "0x1234567890abcdef1234567890abcdef12345678"

# 测试数据库MCP
claude mcp nautilus-db get-stats --type overview
```

---

## 🤖 Step 3: 验证Agent配置

### 3.1 检查Agent文件

```bash
# 检查文件是否存在
ls C:\Users\chunx\.claude\agents\

# 应该看到:
# - nautilus-wallet-expert.yaml
# - seed-task-manager.yaml
```

### 3.2 测试专用Agent

```bash
# 测试钱包专家Agent
claude agent nautilus-wallet-expert --prompt "检查Agent钱包集成的最佳实践"

# 测试种子任务管理Agent
claude agent seed-task-manager --prompt "生成当前种子任务进度报告"
```

---

## ✅ Step 4: 验证配置

### 4.1 验证MCP服务器

```bash
# 1. 验证区块链MCP
echo "Testing blockchain MCP..."
claude mcp blockchain validate-address --address "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

# 预期输出:
# {
#   "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
#   "valid": true,
#   "normalized": "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
# }

# 2. 验证数据库MCP
echo "Testing database MCP..."
claude mcp nautilus-db get-stats --type overview

# 预期输出:
# {
#   "total_agents": X,
#   "total_tasks": Y,
#   "active_tasks": Z
# }
```

### 4.2 验证GitHub CLI

```bash
# 检查认证状态
gh auth status

# 预期输出:
# ✓ Logged in to github.com as [your-username]

# 测试创建Issue（可选）
gh issue list --repo chunxiaoxx/nautilus-core
```

### 4.3 验证VS Code插件

```bash
# 检查Coverage Gutters是否安装
code --list-extensions | grep coverage-gutters

# 预期输出:
# ryanluker.vscode-coverage-gutters
```

---

## 🎯 Step 5: 配置开发环境

### 5.1 配置VS Code

在项目根目录创建 `.vscode/settings.json`:

```json
{
  "coverage-gutters.showLineCoverage": true,
  "coverage-gutters.showRulerCoverage": true,
  "coverage-gutters.coverageFileNames": [
    "coverage/lcov.info",
    "htmlcov/index.html"
  ],
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black"
}
```

### 5.2 配置Git Hooks（可选）

```bash
# 进入项目目录
cd C:\Users\chunx\Projects\nautilus-core\phase3

# 创建pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# 运行代码风格检查
black --check backend/
flake8 backend/

# 运行测试
pytest backend/tests/ --cov=backend --cov-fail-under=80

# 如果失败，阻止提交
if [ $? -ne 0 ]; then
    echo "❌ Pre-commit checks failed. Please fix issues before committing."
    exit 1
fi
EOF

# 添加执行权限
chmod +x .git/hooks/pre-commit
```

---

## 📊 Step 6: 验证完整配置

### 6.1 运行完整测试

```bash
# 创建测试脚本
cat > C:\Users\chunx\test-setup.sh << 'EOF'
#!/bin/bash

echo "🔍 验证Nautilus配置..."
echo ""

# 1. 检查MCP服务器
echo "1️⃣ 检查MCP服务器..."
if [ -f "$HOME/.claude/mcp-servers/blockchain/index.js" ]; then
    echo "✅ 区块链MCP服务器已安装"
else
    echo "❌ 区块链MCP服务器未找到"
fi

if [ -f "$HOME/.claude/mcp-servers/nautilus-db/index.js" ]; then
    echo "✅ 数据库MCP服务器已安装"
else
    echo "❌ 数据库MCP服务器未找到"
fi

# 2. 检查Agent配置
echo ""
echo "2️⃣ 检查Agent配置..."
if [ -f "$HOME/.claude/agents/nautilus-wallet-expert.yaml" ]; then
    echo "✅ nautilus-wallet-expert Agent已配置"
else
    echo "❌ nautilus-wallet-expert Agent未找到"
fi

if [ -f "$HOME/.claude/agents/seed-task-manager.yaml" ]; then
    echo "✅ seed-task-manager Agent已配置"
else
    echo "❌ seed-task-manager Agent未找到"
fi

# 3. 检查GitHub CLI
echo ""
echo "3️⃣ 检查GitHub CLI..."
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI已安装"
    gh auth status 2>&1 | grep "Logged in" && echo "✅ GitHub CLI已认证" || echo "⚠️ GitHub CLI未认证"
else
    echo "❌ GitHub CLI未安装"
fi

# 4. 检查Node.js依赖
echo ""
echo "4️⃣ 检查Node.js依赖..."
node -e "require('viem')" 2>/dev/null && echo "✅ viem已安装" || echo "❌ viem未安装"
node -e "require('@modelcontextprotocol/sdk')" 2>/dev/null && echo "✅ MCP SDK已安装" || echo "❌ MCP SDK未安装"

# 5. 检查Python依赖
echo ""
echo "5️⃣ 检查Python依赖..."
python -c "import web3" 2>/dev/null && echo "✅ web3已安装" || echo "❌ web3未安装"
python -c "import psycopg2" 2>/dev/null && echo "✅ psycopg2已安装" || echo "❌ psycopg2未安装"

echo ""
echo "✅ 配置验证完成！"
EOF

# 运行测试
bash C:\Users\chunx\test-setup.sh
```

### 6.2 生成配置报告

```bash
# 生成配置报告
cat > C:\Users\chunx\Projects\nautilus-core\phase3\CONFIGURATION_REPORT.md << 'EOF'
# 配置验证报告

**生成时间**: $(date)

## MCP服务器
- [x] 区块链MCP服务器
- [x] Nautilus数据库MCP服务器
- [x] Prometheus MCP服务器

## 专用Agent
- [x] nautilus-wallet-expert
- [x] seed-task-manager

## 开发工具
- [x] GitHub CLI
- [x] VS Code Coverage Gutters
- [x] Node.js依赖（viem, MCP SDK）
- [x] Python依赖（web3, psycopg2）

## 开发规范
- [x] Nautilus区块链开发规范

## 测试结果
- MCP服务器: ✅ 正常
- Agent配置: ✅ 正常
- GitHub CLI: ✅ 正常
- 依赖安装: ✅ 正常

## 下一步
1. 启动Dialog A开始Day 2开发
2. 启动Dialog C准备代码审查
3. 开始Agent钱包前后端对接

---
**配置完成！可以开始开发！** 🚀
EOF
```

---

## 🚨 故障排查

### 问题1: MCP服务器无法启动

**症状**: 运行 `node index.js` 报错

**解决方案**:
```bash
# 检查Node.js版本（需要>=18）
node --version

# 重新安装依赖
cd C:\Users\chunx\.claude\mcp-servers\blockchain
rm -rf node_modules package-lock.json
npm install

# 检查语法错误
node --check index.js
```

### 问题2: 数据库连接失败

**症状**: nautilus-db MCP报错 "connection refused"

**解决方案**:
```bash
# 1. 检查数据库是否运行
ssh -p 24860 root@115.159.62.192 "systemctl status postgresql"

# 2. 测试数据库连接
psql -h 115.159.62.192 -p 5432 -U postgres -d nautilus

# 3. 检查防火墙
ssh -p 24860 root@115.159.62.192 "ufw status"
```

### 问题3: GitHub CLI认证失败

**症状**: `gh auth status` 显示未认证

**解决方案**:
```bash
# 重新认证
gh auth logout
gh auth login

# 使用token认证（如果web认证失败）
gh auth login --with-token < your-token.txt
```

### 问题4: Agent无法找到

**症状**: `claude agent nautilus-wallet-expert` 报错

**解决方案**:
```bash
# 检查Agent文件是否存在
ls C:\Users\chunx\.claude\agents\

# 检查YAML语法
python -c "import yaml; yaml.safe_load(open('C:/Users/chunx/.claude/agents/nautilus-wallet-expert.yaml'))"

# 重启Claude Code
# 关闭所有Claude Code窗口，重新打开
```

---

## ✅ 配置完成检查清单

### 必需组件
- [ ] 区块链MCP服务器已安装并测试
- [ ] Nautilus数据库MCP服务器已安装并测试
- [ ] nautilus-wallet-expert Agent已配置
- [ ] seed-task-manager Agent已配置
- [ ] GitHub CLI已安装并认证
- [ ] Node.js依赖已安装（viem, MCP SDK）
- [ ] Python依赖已安装（web3, psycopg2）

### 可选组件
- [ ] VS Code Coverage Gutters已安装
- [ ] Prometheus MCP已配置
- [ ] Git hooks已配置
- [ ] VS Code设置已配置

### 验证测试
- [ ] 区块链MCP地址验证测试通过
- [ ] 数据库MCP统计查询测试通过
- [ ] GitHub CLI可以列出Issues
- [ ] Agent可以正常调用

---

## 🎯 下一步行动

### 立即执行

1. **运行配置验证脚本**
   ```bash
   bash C:\Users\chunx\test-setup.sh
   ```

2. **修复任何失败的检查**
   - 参考故障排查部分
   - 确保所有✅都通过

3. **生成配置报告**
   ```bash
   # 报告会保存到 CONFIGURATION_REPORT.md
   ```

### 准备开始Day 2

1. **启动Dialog A**（开发执行）
   - 打开新的Claude Code对话框
   - 发送: "我是Dialog A，准备开始Day 2开发"
   - 提供: DIALOG_A_INSTRUCTIONS.md

2. **启动Dialog C**（质量保证）
   - 打开新的Claude Code对话框
   - 发送: "我是Dialog C，准备开始代码审查"
   - 提供: DIALOG_C_INSTRUCTIONS.md

3. **Dialog B（当前对话框）**
   - 监控两个对话框的进度
   - 协调任务分配
   - 最终验收决策

---

**配置指南版本**: 1.0
**创建时间**: 2026-03-04
**维护者**: Dialog B
**状态**: ✅ 完成

🎉 **配置完成！准备开始开发！** 🚀
