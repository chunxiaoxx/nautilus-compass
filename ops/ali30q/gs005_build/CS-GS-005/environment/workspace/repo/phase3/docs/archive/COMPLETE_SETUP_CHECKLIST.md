# 完整启用清单和执行脚本

**创建时间**: 2026-03-06
**目标**: 一键启用所有MCP、工具、技能

---

## ✅ 执行清单

### Phase 1: 准备工作（5分钟）

```bash
# 1. 安装uv
pip install uv

# 2. 安装gh CLI
winget install GitHub.cli

# 3. 登录GitHub
gh auth login

# 4. 备份现有配置
cp ~/.claude/mcp_settings.json ~/.claude/mcp_settings.json.backup
```

### Phase 2: 获取API密钥（10分钟）

**GitHub Token**:
1. 访问: https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限: repo, read:org, read:user
4. 生成并复制token
5. 保存到安全位置

**Brave Search API** (可选):
1. 访问: https://brave.com/search/api/
2. 注册账号
3. 获取API key
4. 保存到安全位置

### Phase 3: 应用配置（2分钟）

```bash
# 1. 复制完整配置
cp ~/.claude/mcp_settings_full.json ~/.claude/mcp_settings.json

# 2. 编辑配置文件
# 替换 YOUR_GITHUB_TOKEN_HERE 为你的GitHub token
# 替换 YOUR_BRAVE_API_KEY_HERE 为你的Brave API key（可选）

# Windows用户使用记事本编辑
notepad ~/.claude/mcp_settings.json

# 或使用vim
vim ~/.claude/mcp_settings.json
```

### Phase 4: 重启和验证（3分钟）

```bash
# 1. 关闭所有Claude Code窗口

# 2. 重新打开Claude Code

# 3. 测试MCP服务器
# 在Claude Code中输入以下命令测试
```

**测试命令**:
```
# 测试GitHub MCP
列出我的GitHub仓库

# 测试fetch MCP
获取https://docs.claude.com的内容

# 测试postgres MCP
列出nautilus数据库的所有表

# 测试git MCP
显示当前git状态

# 测试blockchain MCP
查询Base链上的USDC余额
```

---

## 🔧 一键配置脚本

### Windows PowerShell脚本

创建文件 `setup_mcp.ps1`:

```powershell
# Claude Code MCP完整配置脚本
Write-Host "开始配置Claude Code MCP服务器..." -ForegroundColor Green

# 1. 检查uv
Write-Host "`n检查uv安装..." -ForegroundColor Yellow
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "安装uv..." -ForegroundColor Yellow
    pip install uv
} else {
    Write-Host "uv已安装 ✓" -ForegroundColor Green
}

# 2. 检查gh CLI
Write-Host "`n检查gh CLI安装..." -ForegroundColor Yellow
if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "安装gh CLI..." -ForegroundColor Yellow
    winget install GitHub.cli
} else {
    Write-Host "gh CLI已安装 ✓" -ForegroundColor Green
}

# 3. 备份现有配置
Write-Host "`n备份现有配置..." -ForegroundColor Yellow
$mcpConfig = "$env:USERPROFILE\.claude\mcp_settings.json"
if (Test-Path $mcpConfig) {
    Copy-Item $mcpConfig "$mcpConfig.backup"
    Write-Host "配置已备份 ✓" -ForegroundColor Green
}

# 4. 提示输入API密钥
Write-Host "`n请输入API密钥:" -ForegroundColor Yellow
$githubToken = Read-Host "GitHub Token (必需)"
$braveApiKey = Read-Host "Brave API Key (可选，直接回车跳过)"

# 5. 生成配置文件
Write-Host "`n生成MCP配置..." -ForegroundColor Yellow

$config = @{
    mcpServers = @{
        blockchain = @{
            command = "node"
            args = @("C:\Users\chunx\.claude\mcp-servers\blockchain\index.js")
            env = @{}
            disabled = $false
            autoApprove = @("*")
        }
        "nautilus-db" = @{
            command = "node"
            args = @("C:\Users\chunx\.claude\mcp-servers\nautilus-db\index.js")
            env = @{
                DB_USER = "postgres"
                DB_PASSWORD = "DRKcx30190310@"
            }
            disabled = $false
            autoApprove = @("*")
        }
        prometheus = @{
            command = "mcp-prometheus"
            args = @("--url", "http://115.159.62.192:9090")
            env = @{}
            disabled = $false
            autoApprove = @("*")
        }
        github = @{
            command = "uvx"
            args = @("mcp-server-github")
            env = @{
                GITHUB_PERSONAL_ACCESS_TOKEN = $githubToken
            }
            disabled = $false
            autoApprove = @("search_repositories", "get_file_contents", "list_commits")
        }
        fetch = @{
            command = "uvx"
            args = @("mcp-server-fetch")
            env = @{}
            disabled = $false
            autoApprove = @("fetch")
        }
        filesystem = @{
            command = "uvx"
            args = @("mcp-server-filesystem", "C:\Users\chunx\Projects")
            env = @{}
            disabled = $false
            autoApprove = @("read_file", "list_directory")
        }
        postgres = @{
            command = "uvx"
            args = @("mcp-server-postgres", "postgresql://postgres:DRKcx30190310@@localhost:5432/nautilus")
            env = @{}
            disabled = $false
            autoApprove = @("query", "list_tables")
        }
        git = @{
            command = "uvx"
            args = @("mcp-server-git", "--repository", "C:\Users\chunx\Projects\nautilus-core")
            env = @{}
            disabled = $false
            autoApprove = @("git_status", "git_diff", "git_log")
        }
        memory = @{
            command = "uvx"
            args = @("mcp-server-memory")
            env = @{}
            disabled = $false
            autoApprove = @("*")
        }
        time = @{
            command = "uvx"
            args = @("mcp-server-time")
            env = @{}
            disabled = $false
            autoApprove = @("*")
        }
        "sequential-thinking" = @{
            command = "uvx"
            args = @("mcp-server-sequential-thinking")
            env = @{}
            disabled = $false
            autoApprove = @("*")
        }
    }
}

# 添加Brave Search（如果提供了API key）
if ($braveApiKey) {
    $config.mcpServers["brave-search"] = @{
        command = "uvx"
        args = @("mcp-server-brave-search")
        env = @{
            BRAVE_API_KEY = $braveApiKey
        }
        disabled = $false
        autoApprove = @("brave_web_search")
    }
}

# 6. 保存配置
$configJson = $config | ConvertTo-Json -Depth 10
$configJson | Out-File -FilePath $mcpConfig -Encoding UTF8
Write-Host "配置已保存 ✓" -ForegroundColor Green

# 7. 完成
Write-Host "`n配置完成！" -ForegroundColor Green
Write-Host "请重启Claude Code以应用新配置。" -ForegroundColor Yellow
Write-Host "`n测试命令:" -ForegroundColor Cyan
Write-Host "  - 列出我的GitHub仓库" -ForegroundColor White
Write-Host "  - 获取https://docs.claude.com的内容" -ForegroundColor White
Write-Host "  - 列出nautilus数据库的所有表" -ForegroundColor White
```

**运行脚本**:
```powershell
# 在PowerShell中运行
.\setup_mcp.ps1
```

---

## 📋 手动配置步骤

如果脚本无法运行，手动执行以下步骤：

### 1. 编辑MCP配置

```bash
# 打开配置文件
notepad C:\Users\chunx\.claude\mcp_settings.json
```

### 2. 替换以下内容

**查找**: `YOUR_GITHUB_TOKEN_HERE`
**替换为**: 你的GitHub token (ghp_xxxx...)

**查找**: `YOUR_BRAVE_API_KEY_HERE`
**替换为**: 你的Brave API key (或删除整个brave-search配置)

### 3. 保存并关闭

### 4. 重启Claude Code

---

## 🎯 验证配置

### 快速验证脚本

创建文件 `verify_mcp.ps1`:

```powershell
Write-Host "验证MCP配置..." -ForegroundColor Green

# 检查配置文件
$mcpConfig = "$env:USERPROFILE\.claude\mcp_settings.json"
if (Test-Path $mcpConfig) {
    Write-Host "✓ MCP配置文件存在" -ForegroundColor Green

    # 读取配置
    $config = Get-Content $mcpConfig | ConvertFrom-Json
    $serverCount = $config.mcpServers.PSObject.Properties.Count
    Write-Host "✓ 配置了 $serverCount 个MCP服务器" -ForegroundColor Green

    # 列出服务器
    Write-Host "`n已配置的MCP服务器:" -ForegroundColor Yellow
    foreach ($server in $config.mcpServers.PSObject.Properties) {
        $disabled = if ($server.Value.disabled) { "(已禁用)" } else { "" }
        Write-Host "  - $($server.Name) $disabled" -ForegroundColor White
    }
} else {
    Write-Host "✗ MCP配置文件不存在" -ForegroundColor Red
}

# 检查工具
Write-Host "`n检查必需工具:" -ForegroundColor Yellow
$tools = @("uv", "gh", "node", "npm")
foreach ($tool in $tools) {
    if (Get-Command $tool -ErrorAction SilentlyContinue) {
        Write-Host "  ✓ $tool" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $tool (未安装)" -ForegroundColor Red
    }
}

Write-Host "`n验证完成！" -ForegroundColor Green
```

**运行验证**:
```powershell
.\verify_mcp.ps1
```

---

## 📚 完整文档索引

### 配置文档
1. `FULL_MCP_SETUP_GUIDE.md` - MCP完整设置指南
2. `WEB_AND_MCP_TROUBLESHOOTING.md` - 故障排查
3. `CLAUDE_CODE_CONFIGURATION_SUMMARY.md` - 配置总结

### 规则文档
4. `~/.claude/rules/common/agent-usage.md` - Agent使用指南
5. `~/.claude/rules/common/response-style.md` - 响应风格
6. `~/.claude/rules/common/parallel-execution.md` - 并行执行
7. `~/.claude/rules/common/tool-priority.md` - 工具优先级
8. `~/.claude/rules/common/task-management.md` - 任务管理

### 项目文档
9. `~/.claude/rules/nautilus/project-rules.md` - 项目规则
10. `~/.claude/rules/nautilus/team-mode.md` - 团队模式
11. `CLAUDE.md` - 项目配置

---

## ✅ 最终检查清单

配置完成后，确认以下项目：

### 工具安装
- [ ] uv已安装并在PATH中
- [ ] gh CLI已安装
- [ ] gh已登录GitHub
- [ ] node和npm已安装

### MCP配置
- [ ] mcp_settings.json已更新
- [ ] GitHub token已配置
- [ ] Brave API key已配置（可选）
- [ ] 所有路径正确（Windows路径使用\\）

### 功能验证
- [ ] Claude Code已重启
- [ ] 可以列出GitHub仓库
- [ ] 可以获取网页内容
- [ ] 可以查询数据库
- [ ] 可以查看git状态

### 规则加载
- [ ] CLAUDE.md存在于项目根目录
- [ ] ~/.claude/rules/目录包含所有规则文件
- [ ] 新会话自动加载规则

---

## 🎉 完成！

所有MCP服务器、工具和技能已启用！

**下一步**:
1. 重启Claude Code
2. 测试各个MCP服务器
3. 开始使用增强功能
4. 继续Week 2开发工作

**如遇问题**:
- 查看 `WEB_AND_MCP_TROUBLESHOOTING.md`
- 检查 `~/.claude/logs/mcp-*.log`
- 运行 `verify_mcp.ps1` 验证配置
