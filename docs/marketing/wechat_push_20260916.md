# 微信推广三件套(朋友圈/群聊/安装咒语 · 2026-09-16)

> 用法:朋友圈版直接发(配一张架构文 HTML 截图或 repo 首图);群聊版整段贴;
> **安装咒语是核心创新**——微信分享的基本单位就是消息,把"上手"做成一条
> 可转发的消息:用户复制→粘给自己的 AI→AI 自己装好。
> 数字纪律:只用可复算集(0.890 vs 0.774/$3.50),零黑话,星标请求自然收尾。

## 一 · 朋友圈版(5 行内,直接发)

做了 130 天的一个开源项目:给 AI 助手装"长期记忆"——它记住你上周说过的每个决定,新会话不再从零开始。
写入零大模型调用,数据不出你电脑;500 题基准检索全量超 mem0(P@1 0.890 vs 0.774),全部数字可复算($3.50 一条命令)。
最简单的试用方式:把我下面这条消息直接转发给你的 AI 助手,它自己会装好 👇
[安装咒语——见群聊版引用块,朋友圈可跟一条评论贴]
GitHub 星标支持一下:github.com/chunxiaoxx/nautilus-compass 🌟

## 二 · 群聊版(整段贴,含咒语)

各位,分享一个我们做的开源项目 nautilus-compass——AI 助手的长期记忆层。

解决一个大家都烦的事:AI 每次新会话都失忆,上周定的规范、踩过的坑、项目背景全要重新交代。装上之后这些自动留存、相关时自动召回,还有"漂移检测"防止 AI 重犯老错。特点:写入时不调大模型(省钱+数据不出本机),跨 Claude Code/Cursor/Cline/WorkBuddy 都能用;在 LongMemEval 500 题基准上检索全量对打 mem0,P@1 0.890 vs 0.774——这个数字任何人 $3.50 就能复现,我们的每个对外数字都带签名证据包。

**最方便的上手方式:把下面这段直接复制发给你的 AI 助手,它会自己配置好:**

> 【帮我安装 nautilus-compass 记忆层】
> 请帮我接入开源 AI 记忆层 nautilus-compass(github.com/chunxiaoxx/nautilus-compass,Modified MIT 开源)。
> 二选一:
> A. 如果你有命令行权限,执行:
> git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
> bash ~/.claude/plugins/nautilus-compass/install.sh
> bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
> 完成后验证:recall 一条我们之前的对话,看能否命中。
> B. 如果你是 WorkBuddy 这类带"连接器"功能的应用:在连接器管理→自定义连接器里添加 MCP 服务,地址 https://compass.nautilus.social/mcp/(先在该网站注册拿一个 Bearer token);或按应用说明添加本地命令 python ~/.claude/plugins/nautilus-compass/mcp_server.py。
> 遇到问题把报错发我。装好后告诉我你记住了什么。

觉得有用的话帮忙点个星标:github.com/chunxiaoxx/nautilus-compass 🌟(README 里有完整文档和双语技能卡)

## 三 · 安装咒语(独立版,任意场景转发)

【帮我安装 nautilus-compass 记忆层】
请帮我接入开源 AI 记忆层 nautilus-compass(github.com/chunxiaoxx/nautilus-compass)。
A(有命令行):git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass && bash ~/.claude/plugins/nautilus-compass/install.sh && bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
B(WorkBuddy 等带连接器的应用):自定义连接器添加 MCP 地址 https://compass.nautilus.social/mcp/ + Bearer token(网站注册即得)
装好验证一条:问我一个之前会话里的决定,看能否召回。报错发回来。

## 使用建议

- 朋友圈黄金时段 21:00-22:00;群聊挑活跃群先发,附一张自己实测截图(比如
  你的 agent 召回了一条几天前的对话)比任何文案都有说服力
- 咒语已被设计为**自含**(A/B 双路+验证步+回错兜底),agent 拿到不会死路
- 若群里有人问"安全吗":数据不出本机(A 路全本地)/云端版用户隔离+scoped
  token(B 路),两层都如实答
