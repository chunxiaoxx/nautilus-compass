---
name: orgfuel-ORGM-discord-cdp-chrome154-re-97069a6bc0
description: "--- name: discord-cdp-chrome154-recipe-20260927 description:"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-discord-cdp-chrome154-re
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: discord-cdp-chrome154-recipe-20260927
description: Chrome154 下 Discord CDP 发帖配方四坑(placeholder 撞类名/Enter 唯一通道=CDP text\r/nav 废 context/f-string 拼 JS 大括号)与 9224 重启配方
metadata: 
  node_type: memory
  type: project
  originSessionId: d0c2a295-24b5-4f89-91ae-92a6be183219
  modified: 2026-09-26T10:42:51.165Z
fact_status: inferred
---

2026-09-27 BC1 发布日,scripts/post_discord.py(9/24 Chrome153 实证配方)在 Chrome 154 全线失效,四根因全勘误后回写仓(commit fc2c1311),实证 GREEN(BC1 帖上墙 show-and-tell,msgId 1553355737218945064):

1. **placeholder 撞类名**:Discord 改版后 placeholder DIV 也带 `slateTextArea` 类,`querySelector('[class*=slateTextArea]')` 抓到 placeholder(`isContentEditable=false`)→ focus 漂到按钮 → `Input.insertText` 落空;且"residue≤25=已发"的判据把没插进去(占位符"Message #show-and-tell"恰 20 字)误判成发送成功。修:选择器 `div[role=textbox][class*
