# Publish guide · nautilus-compass-mcp

## 真预 publish 验证(本地)

```bash
cd C:/Users/chunx/.claude/plugins/nautilus-compass/npm

# 1. 真验 package
npm pack --dry-run
# expect: 4 files · LICENSE / README.md / bin/cli.js / package.json

# 2. 真测 selftest(需先 pip install nautilus-compass)
node bin/cli.js --selftest
# expect: OK: python3 + nautilus-compass found
```

## 真 publish(用户做 · 我无 npm token)

```bash
cd C:/Users/chunx/.claude/plugins/nautilus-compass/npm

# 1. npm login(若未登)
npm login

# 2. publish dry-run 真检查
npm publish --dry-run --access public

# 3. 真 publish(@nautilus scope · public access)
npm publish --access public

# 4. 真 verify
npm view nautilus-compass-mcp
```

## 真 post-publish 推广

1. **Twitter / X** 真发(原创 · 真有 paper SOTA tier 数据)
2. **Show HN** 真发(GitHub link + LongMemEval-S 56.6% 真测)
3. **Cursor / Cline / Claude Desktop** 真社区(MCP server 真分享)
4. **dev.to / Medium** 真写飞轮真故事(用 Agent J 看板 + 24h 真闭环数据)

## 真 troubleshoot

| 真问题 | 真修 |
|---|---|
| 403 publish denied | scope @nautilus 真 register · npm access public |
| Cannot find module | check bin/cli.js shebang(`#!/usr/bin/env node`)+ chmod +x |
| selftest fail · python3 not found | 用户自己装 python · 不是 publisher 责任 |

## 真版本管理

```bash
# patch · bug fix
npm version patch  # 0.9.0-dev → 0.9.1

# minor · 新功能
npm version minor  # 0.9.x → 0.10.0

# major · breaking
npm version major  # 0.9.x → 1.0.0

# 真 publish next
npm publish --access public
```

## 真 cross-link 真 GitHub release

```bash
# tag + push
git tag -a v0.9.0 -m "Release 0.9.0 · npm + MCP"
git push origin v0.9.0

# 真 GitHub release
gh release create v0.9.0 --title "v0.9.0 · npm package live" --notes "..."
```
