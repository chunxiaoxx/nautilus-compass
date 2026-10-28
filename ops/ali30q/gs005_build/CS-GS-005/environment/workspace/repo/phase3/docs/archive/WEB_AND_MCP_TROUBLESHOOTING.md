# 网页访问和MCP问题解决方案

**问题诊断时间**: 2026-03-06
**问题**: Claude Code无法打开网页，无法调用浏览器工具和GitHub MCP

---

## 🔍 问题诊断

### 问题1: 代理配置导致网络访问受限

**当前配置** (`~/.claude/settings.json`):
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:52000"
  }
}
```

**问题**:
- 使用本地代理（127.0.0.1:52000）
- WebFetch工具可能被代理阻止
- 外部网络访问受限

### 问题2: 缺少GitHub和浏览器MCP配置

**当前MCP服务器** (`~/.claude/mcp_settings.json`):
- ✅ blockchain
- ✅ nautilus-db
- ✅ prometheus
- ❌ **没有GitHub MCP**
- ❌ **没有浏览器/web MCP**

---

## 🔧 解决方案

### 方案1: 配置GitHub MCP（推荐）

**添加GitHub MCP服务器**:

```json
{
  "mcpServers": {
    "blockchain": {
      "command": "node",
      "args": ["C:\\Users\\chunx\\.claude\\mcp-servers\\blockchain\\index.js"],
      "env": {}
    },
    "nautilus-db": {
      "command": "node",
      "args": ["C:\\Users\\chunx\\.claude\\mcp-servers\\nautilus-db\\index.js"],
      "env": {
        "DB_USER": "postgres",
        "DB_PASSWORD": "DRKcx30190310@"
      }
    },
    "prometheus": {
      "command": "mcp-prometheus",
      "args": ["--url", "http://115.159.62.192:9090"],
      "env": {}
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
      }
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {}
    }
  }
}
```

**获取GitHub Token**:
1. 访问: https://github.com/settings/tokens
2. 生成新token (classic)
3. 权限: repo, read:org, read:user
4. 复制token替换上面的`your_github_token_here`

---

### 方案2: 使用gh CLI（替代方案）

**如果GitHub MCP不工作，使用gh命令**:

```bash
# 安装gh CLI
winget install GitHub.cli

# 登录
gh auth login

# 使用gh命令代替MCP
gh pr list
gh issue list
gh repo view
```

**在Claude Code中使用**:
```bash
# 查看PR
gh pr view 123

# 查看issue
gh issue view 456

# 创建PR
gh pr create --title "..." --body "..."
```

---

### 方案3: WebFetch工具配置

**问题**: WebFetch可能被代理阻止

**解决方法1: 配置代理白名单**

如果你的代理支持，添加白名单：
```
github.com
docs.claude.com
*.anthropic.com
```

**解决方法2: 临时禁用代理**

编辑 `~/.claude/settings.json`:
```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED",
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:52000",
    "NO_PROXY": "github.com,docs.claude.com"
  },
  "model": "sonnet[1m]",
  "skipDangerousModePermissionPrompt": true
}
```

**解决方法3: 使用MCP fetch服务器**

MCP fetch服务器可以绕过某些限制：
```json
"fetch": {
  "command": "uvx",
  "args": ["mcp-server-fetch"],
  "env": {}
}
```

---

### 方案4: 检查网络连接

**测试网络访问**:
```bash
# 测试GitHub访问
curl -I https://github.com

# 测试Claude文档访问
curl -I https://docs.claude.com

# 测试代理
curl -x http://127.0.0.1:52000 -I https://github.com
```

---

## 📋 实施步骤

### Step 1: 安装必要工具

```bash
# 安装uv（Python包管理器，用于MCP服务器）
pip install uv

# 或使用官方安装脚本
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装gh CLI
winget install GitHub.cli
```

### Step 2: 配置GitHub MCP

**编辑MCP配置**:
```bash
# 备份现有配置
cp ~/.claude/mcp_settings.json ~/.claude/mcp_settings.json.backup

# 编辑配置添加GitHub MCP
# 使用上面的JSON配置
```

### Step 3: 获取GitHub Token

1. 访问: https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限:
   - ✅ repo (完整仓库访问)
   - ✅ read:org (读取组织)
   - ✅ read:user (读取用户信息)
4. 生成并复制token
5. 添加到MCP配置的`GITHUB_PERSONAL_ACCESS_TOKEN`

### Step 4: 重启Claude Code

```bash
# 重启Claude Code以加载新配置
# 或使用命令
claude code restart
```

### Step 5: 测试MCP连接

**测试GitHub MCP**:
```
# 在Claude Code中测试
列出我的GitHub仓库
```

**测试fetch MCP**:
```
# 在Claude Code中测试
获取https://docs.claude.com的内容
```

---

## 🔍 故障排查

### 问题: MCP服务器无法启动

**检查日志**:
```bash
# 查看Claude Code日志
cat ~/.claude/logs/mcp-*.log
```

**常见原因**:
1. uv未安装或不在PATH中
2. GitHub token无效
3. 网络连接问题
4. 代理配置冲突

### 问题: WebFetch仍然失败

**使用gh CLI替代**:
```bash
# 代替WebFetch获取GitHub内容
gh api repos/owner/repo/contents/file.md
```

**使用curl替代**:
```bash
# 代替WebFetch获取网页内容
curl -s https://example.com
```

### 问题: 代理冲突

**临时禁用代理测试**:
```bash
# 临时移除代理配置
mv ~/.claude/settings.json ~/.claude/settings.json.backup

# 创建无代理配置
echo '{"model": "sonnet[1m]"}' > ~/.claude/settings.json

# 测试是否工作
# 如果工作，说明是代理问题
```

---

## 🎯 推荐配置

### 最小可用配置

**~/.claude/mcp_settings.json**:
```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {}
    }
  }
}
```

### 完整配置（包含现有服务器）

**~/.claude/mcp_settings.json**:
```json
{
  "mcpServers": {
    "blockchain": {
      "command": "node",
      "args": ["C:\\Users\\chunx\\.claude\\mcp-servers\\blockchain\\index.js"],
      "env": {}
    },
    "nautilus-db": {
      "command": "node",
      "args": ["C:\\Users\\chunx\\.claude\\mcp-servers\\nautilus-db\\index.js"],
      "env": {
        "DB_USER": "postgres",
        "DB_PASSWORD": "DRKcx30190310@"
      }
    },
    "prometheus": {
      "command": "mcp-prometheus",
      "args": ["--url", "http://115.159.62.192:9090"],
      "env": {}
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {}
    }
  }
}
```

---

## 📚 参考资源

### MCP服务器文档
- GitHub MCP: https://github.com/modelcontextprotocol/servers
- Fetch MCP: https://github.com/modelcontextprotocol/servers/tree/main/src/fetch

### Claude Code文档
- MCP配置: https://docs.claude.com/en/docs/claude-code/mcp
- WebFetch工具: https://docs.claude.com/en/docs/claude-code/tools

### 工具安装
- uv安装: https://docs.astral.sh/uv/getting-started/installation/
- gh CLI: https://cli.github.com/

---

## ✅ 验证清单

配置完成后验证：

- [ ] uv已安装并在PATH中
- [ ] GitHub token已生成并配置
- [ ] MCP配置文件已更新
- [ ] Claude Code已重启
- [ ] 可以列出GitHub仓库
- [ ] 可以获取网页内容
- [ ] WebFetch工具正常工作

---

**如果问题仍然存在，请提供**:
1. `~/.claude/logs/mcp-*.log` 日志内容
2. 具体的错误信息
3. 网络环境（是否在公司网络、VPN等）
