# 启用GitHub MCP

## 获取GitHub Token

1. 访问: https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限:
   - ✅ repo (完整仓库访问)
   - ✅ read:org (读取组织)
   - ✅ read:user (读取用户信息)
4. 生成并复制token

## 配置Token

编辑 `~/.claude/mcp_settings.json`:

找到第91行的 `"GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_GITHUB_TOKEN_HERE"`

替换 `YOUR_GITHUB_TOKEN_HERE` 为你的token

然后将第101行的 `"disabled": true` 改为 `"disabled": false`

## 重启Claude Code

关闭所有窗口，重新打开

## 测试

在Claude Code中输入：
```
列出我的GitHub仓库
```
