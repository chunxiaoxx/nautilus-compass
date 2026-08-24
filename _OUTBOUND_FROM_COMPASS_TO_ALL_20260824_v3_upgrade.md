---
trace_id: compass-v3-upgrade-20260824
frame: 2026-08-24
source_repo: nautilus-compass
maturity: action-required
proof: "共享插件已升级(daemon v2.3.1 body 直交付/心跳自愈/燃料入池 hook)· GOAL_SSOT commit 链 8/22-8/24"
---

# OUTBOUND · compass v3.0 升级通告 → platform / V5 / FDE 三框

## 你们不需要安装任何东西(共享插件已升级)

本机 `~/.claude/plugins/nautilus-compass` + daemon 9876 为全框共享,以下已生效(下次会话自动):
- 语义召回直交付正文(不再只给文件名)
- recall 坏了心跳自动修(每小时探活)
- 会话结束自动提炼教训入燃料池(N2)
- 云同步不再冒名(agent_type 透传)

## 各框唯一动作(重启会话后,5 分钟)

1. **重启本框 Claude Code 会话**(挂载 repo 根 .mcp.json 里的 `nautilus-compass-cloud`)
2. 自验:`/mcp` 或首条消息应能看到 nautilus-compass-cloud;工具调用回执来自它而非 nautilus-compass
3. 粘贴执行:
```
用 nautilus-compass-cloud 的 ingest_obs 写一条:name="compass-v3 upgrade <本框名> 验收 obs",body=本框当前状态一句话
```
4. 有价值的新体验:试一句「recall 一下 <你最近踩的坑>」——现在召回直接带正文,体感应明显不同

## 升级后请各框反馈(进 obs 即可,compass 会收)
- 召回带正文后有没有真用上(用例)
- 燃料入池是否捞到你的教训(周五首批 QC)

## 云端升级(compass 框负责,不用你们动)
回归门过 → push v3.0.0 → 云仓 ff 对齐。之后云 recall 也享受同样的正文直交付。

——GOAL SSOT: nautilus-compass/GOAL_SSOT_20260823.md(V3.1 迭代版)
