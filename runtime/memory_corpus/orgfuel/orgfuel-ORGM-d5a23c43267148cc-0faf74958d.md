---
name: orgfuel-ORGM-d5a23c43267148cc-0faf74958d
description: "记忆条目 discord-cdp-chrome154-recipe-20260927.md 2026-09-27 BC1"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-d5a23c43267148cc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 discord-cdp-chrome154-recipe-20260927.md
2026-09-27 BC1 发布日,scripts/post_discord.py(9/24 Chrome153 实证配方)在 Chrome 154 全线失效,四根因全勘误后回写仓(commit fc2c1311),实证 GREEN(BC1 帖上墙 show-and-tell,msgId 1553355737218945064):

1. **placeholder 撞类名**:Discord 改版后 placeholder DIV 也带 `slateTextArea` 类,`querySelector('[class*=slateTextArea]')` 抓到 placeholder(`isContentEditable=false`)→ focus 漂到按钮 → `Input.insertText` 落空;且"residue≤25=已发"的判据把没插进去(占位符"Message #show-and-tell"恰 20 字)误判成发送成功。修:选择器 `div[role=textbox][class*=slateTextArea]`,插入后按目标长度验长。
2. **Enter 唯一有效通道 = CDP `Input.dispatchKeyEvent {type:"keyDown", text:"\r"}` + keyUp**;JS `dispatchEvent(KeyboardEvent)` 在 154 失效(153 曾有效)。
3. **发帖脚本勿内嵌 Page.navigate**:nav 后旧 execution context 报废,evaluate 持续 `EXC:Uncaught` 超过 16s;先 `cdp_tool.py nav` 到位再跑发帖脚本(脚本只校验 
