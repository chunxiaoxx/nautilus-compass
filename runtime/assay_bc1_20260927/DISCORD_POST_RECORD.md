# Discord 发帖记录 · BC1 发布(show-and-tell)

- 发帖时间:2026-09-27(会话机器钟 9/26 18:41;发布日值班会话执行)
- 频道:#show-and-tell(TypeSafe AI 服务器,guild 1483217544214085663,channel 1483217545040232493)
- msgId:1553355737218945064
- 直链:https://discord.com/channels/1483217544214085663/1483217545040232493/1553355737218945064
- 正文源:.post_body.txt(= DISCORD_LAUNCH_DRAFT.md 去存档头,1308 字符)
- 截图:discord_post_landed.png(发后);discord_after_post.png(发前状态)
- 值守盯帖:nav 上方直链读上下文;勿程序化翻历史(mouseWheel 死,见 cdp_tool.py 头注)

## 发帖配方勘误(Chrome 154 实测,回写 scripts/post_discord.py)

1. v1 失效根因:placeholder DIV 现也带 `slateTextArea` 类 → querySelector 抓到
   placeholder(isContentEditable=false)→ focus 漂移 → Input.insertText 落空;
   且 residue<=25 的 break 把"没插进去"(占位符恰 20 字)误判为发送成功。
2. 修法:选择器 `div[role=textbox][class*=slateTextArea]`;插入后按目标长度验长。
3. Enter:JS dispatchEvent(9/24 Chrome153 配方)在 154 失效;唯一有效 =
   CDP `Input.dispatchKeyEvent {type:"keyDown", key:"Enter", text:"\r"}` + keyUp。
4. **勿在发帖脚本里 Page.navigate**——nav 后旧 execution context 报废,evaluate
   持续 EXC:Uncaught;先 cdp_tool.py nav 到位再跑发帖脚本。
5. f-string 拼 JS 的 `{{}}` 转义地狱连续翻车 2 次(多/少一个大括号=
   SyntaxError 无细节);JS 片段一律普通字符串拼接,大括号直书。
6. 读回比对要剥 markdown 符号(`**` 渲染后消失,裸 textContent 比对必假阴性)。
