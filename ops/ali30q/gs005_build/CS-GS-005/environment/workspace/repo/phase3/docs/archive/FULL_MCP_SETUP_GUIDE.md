# 完整MCP和工具启用指南

**创建时间**: 2026-03-06
**目标**: 启用所有可用的MCP服务器、工具和技能

---

## 📊 MCP服务器清单

### 已启用的服务器（当前）
1. ✅ **blockchain** - 区块链交互
2. ✅ **nautilus-db** - Nautilus数据库
3. ✅ **prometheus** - 监控指标

### 推荐启用的服务器（新增）
4. 🆕 **github** - GitHub集成
5. 🆕 **fetch** - 网页获取
6. 🆕 **filesystem** - 文件系统访问
7. 🆕 **brave-search** - 网页搜索
8. 🆕 **postgres** - PostgreSQL数据库
9. 🆕 **git** - Git操作
10. 🆕 **memory** - 持久化记忆
11. 🆕 **puppeteer** - 浏览器自动化
12. 🆕 **sqlite** - SQLite数据库
13. 🆕 **time** - 时间工具
14. 🆕 **sequential-thinking** - 顺序思考

---

## 🚀 快速启用步骤

### Step 1: 安装必要工具

```bash
# 安装uv（Python包管理器）
pip install uv

# 或使用官方脚本
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows用户
pip install uv

# 安装gh CLI
winget install GitHub.cli

# 登录GitHub
gh auth login
```

### Step 2: 获取API密钥

**GitHub Token**:
1. 访问: https://github.com/settings/tokens
2. 生成token (classic)
3. 权限: repo, read:org, read:user
4. 复制token

**Brave Search API** (可选):
1. 访问: https://brave.com/search/api/
2. 注册并获取API key
3. 免费tier: 2000次/月

### Step 3: 备份现有配置

```bash
# 备份当前MCP配置
cp ~/.claude/mcp_settings.json ~/.claude/mcp_settings.json.backup
```

### Step 4: 应用新配置

```bash
# 复制完整配置
cp ~/.claude/mcp_settings_full.json ~/.claude/mcp_settings.json

# 编辑配置，替换API密钥
# YOUR_GITHUB_TOKEN_HERE → 你的GitHub token
# YOUR_BRAVE_API_KEY_HERE → 你的Brave API key（可选）
```

### Step 5: 重启Claude Code

```bash
# 重启Claude Code
# 或关闭所有Claude Code窗口后重新打开
```

---

## 📋 各MCP服务器详细说明

### 1. blockchain (已启用)
**功能**: 区块链交互
**用途**:
- 查询Base链数据
- USDC余额查询
- 交易验证

**工具**:
- `get_balance` - 获取余额
- `get_transaction` - 获取交易
- `estimate_gas` - 估算gas

### 2. nautilus-db (已启用)
**功能**: Nautilus数据库访问
**用途**:
- 查询Agent数据
- 查询任务数据
- 数据库操作

**工具**:
- `query` - 执行SQL查询
- `list_tables` - 列出表
- `describe_table` - 描述表结构

### 3. prometheus (已启用)
**功能**: 监控指标查询
**用途**:
- 查询性能指标
- 监控系统状态
- 生成报告

**工具**:
- `query` - PromQL查询
- `query_range` - 范围查询

### 4. github (新增)
**功能**: GitHub集成
**用途**:
- 搜索仓库
- 读取文件
- 查看PR/Issue
- 提交代码

**工具**:
- `search_repositories` - 搜索仓库
- `get_file_contents` - 获取文件内容
- `list_commits` - 列出提交
- `create_issue` - 创建issue
- `create_pull_request` - 创建PR

**配置**:
```json
"github": {
  "command": "uvx",
  "args": ["mcp-server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
  }
}
```

### 5. fetch (新增)
**功能**: 网页内容获取
**用途**:
- 获取网页内容
- API调用
- 下载文件

**工具**:
- `fetch` - 获取URL内容

**使用示例**:
```
获取https://docs.claude.com的内容
```

### 6. filesystem (新增)
**功能**: 文件系统访问
**用途**:
- 读取项目外文件
- 列出目录
- 监控文件变化

**工具**:
- `read_file` - 读取文件
- `list_directory` - 列出目录
- `get_file_info` - 获取文件信息

### 7. brave-search (新增)
**功能**: 网页搜索
**用途**:
- 搜索最新信息
- 技术文档查找
- 问题解决方案搜索

**工具**:
- `brave_web_search` - 网页搜索

**使用示例**:
```
搜索"FastAPI async database best practices"
```

### 8. postgres (新增)
**功能**: PostgreSQL数据库直接访问
**用途**:
- 执行复杂查询
- 数据库管理
- 性能分析

**工具**:
- `query` - 执行SQL
- `list_tables` - 列出表
- `describe_table` - 描述表

### 9. git (新增)
**功能**: Git操作
**用途**:
- 查看状态
- 查看diff
- 查看历史

**工具**:
- `git_status` - 查看状态
- `git_diff` - 查看差异
- `git_log` - 查看历史
- `git_show` - 查看提交

### 10. memory (新增)
**功能**: 持久化记忆
**用途**:
- 跨会话记忆
- 存储重要信息
- 知识库构建

**工具**:
- `store_memory` - 存储记忆
- `retrieve_memory` - 检索记忆
- `list_memories` - 列出记忆

### 11. puppeteer (新增)
**功能**: 浏览器自动化
**用途**:
- 网页截图
- 自动化测试
- 网页交互

**工具**:
- `puppeteer_navigate` - 导航到URL
- `puppeteer_screenshot` - 截图
- `puppeteer_click` - 点击元素
- `puppeteer_fill` - 填写表单

### 12. sqlite (新增)
**功能**: SQLite数据库
**用途**:
- 本地数据存储
- 测试数据
- 轻量级数据库

**工具**:
- `query` - 执行SQL
- `list_tables` - 列出表

### 13. time (新增)
**功能**: 时间工具
**用途**:
- 获取当前时间
- 时区转换
- 时间计算

**工具**:
- `get_current_time` - 获取当前时间
- `convert_timezone` - 时区转换

### 14. sequential-thinking (新增)
**功能**: 顺序思考工具
**用途**:
- 复杂问题分解
- 逐步推理
- 决策支持

**工具**:
- `think_step_by_step` - 逐步思考

---

## 🎯 使用场景

### Nautilus项目开发

**场景1: 代码审查**
```
使用github MCP查看PR
使用git MCP查看diff
使用code-reviewer agent审查代码
```

**场景2: 性能分析**
```
使用prometheus MCP查询指标
使用postgres MCP分析数据库性能
生成性能报告
```

**场景3: 问题调试**
```
使用brave-search搜索错误信息
使用github MCP查看相关issue
使用sequential-thinking分析问题
```

**场景4: 文档查找**
```
使用fetch MCP获取官方文档
使用brave-search搜索最佳实践
使用memory MCP存储重要信息
```

### 区块链开发

**场景1: 钱包测试**
```
使用blockchain MCP查询余额
使用blockchain MCP验证签名
使用postgres MCP查询数据库
```

**场景2: 交易监控**
```
使用blockchain MCP监控交易
使用prometheus MCP记录指标
使用puppeteer MCP截图区块浏览器
```

---

## ⚙️ 配置优化

### autoApprove设置

**推荐配置**:
```json
{
  "blockchain": {
    "autoApprove": ["*"]  // 自动批准所有blockchain操作
  },
  "github": {
    "autoApprove": [
      "search_repositories",
      "get_file_contents",
      "list_commits"
    ]  // 只自动批准读操作
  },
  "postgres": {
    "autoApprove": ["query", "list_tables"]  // 只自动批准查询
  }
}
```

### disabled设置

**临时禁用不需要的服务器**:
```json
{
  "everart": {
    "disabled": true  // 暂时不需要图片生成
  },
  "puppeteer": {
    "disabled": false  // 需要浏览器自动化
  }
}
```

---

## 🔍 故障排查

### 问题1: uvx命令找不到

**解决**:
```bash
# 确保uv已安装
pip install uv

# 添加到PATH
export PATH="$HOME/.local/bin:$PATH"

# Windows
# 添加 C:\Users\chunx\AppData\Local\Programs\Python\Python311\Scripts 到PATH
```

### 问题2: MCP服务器启动失败

**检查日志**:
```bash
# 查看MCP日志
cat ~/.claude/logs/mcp-*.log

# 查看最新日志
tail -f ~/.claude/logs/mcp-*.log
```

**常见原因**:
- API密钥未配置
- 网络连接问题
- 依赖未安装

### 问题3: GitHub MCP无法连接

**检查token**:
```bash
# 测试token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

**检查权限**:
- repo权限
- read:org权限
- read:user权限

### 问题4: 代理冲突

**临时禁用代理**:
```json
{
  "env": {
    "NO_PROXY": "github.com,api.github.com"
  }
}
```

---

## 📊 验证清单

启用后验证：

### 基础功能
- [ ] uv已安装
- [ ] gh CLI已安装并登录
- [ ] MCP配置文件已更新
- [ ] Claude Code已重启

### MCP服务器
- [ ] blockchain MCP正常
- [ ] nautilus-db MCP正常
- [ ] prometheus MCP正常
- [ ] github MCP正常
- [ ] fetch MCP正常
- [ ] postgres MCP正常
- [ ] git MCP正常
- [ ] memory MCP正常

### 功能测试
- [ ] 可以搜索GitHub仓库
- [ ] 可以获取网页内容
- [ ] 可以查询数据库
- [ ] 可以查看git状态
- [ ] 可以存储和检索记忆

---

## 🎯 下一步

**立即测试**:
1. 重启Claude Code
2. 测试GitHub MCP: "列出我的GitHub仓库"
3. 测试fetch MCP: "获取https://docs.claude.com的内容"
4. 测试postgres MCP: "列出nautilus数据库的所有表"

**持续优化**:
1. 根据使用情况调整autoApprove
2. 禁用不需要的服务器
3. 添加新的MCP服务器

---

**配置文件位置**:
- 完整配置: `~/.claude/mcp_settings_full.json`
- 当前配置: `~/.claude/mcp_settings.json`
- 备份配置: `~/.claude/mcp_settings.json.backup`
