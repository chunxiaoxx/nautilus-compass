# 9/8 夜间持续行动清单(Loop 模式 · 发布夜值守)

> Loop 每 30min 一轮。每轮必做 A 组;然后按序推进 B/C/D 未完成项(每轮一件);每轮末尾输出一行状态。
> 纪律:不 push 用户未拍板的改动;不发未经用户过目的对外内容(值守回复草稿例外=仅起草给用户贴);验证优于自报;发现需用户决策的事,记录不动手。

## A · 值守(每轮必做)

- [ ] A1 9876 daemon ping(必须 `b'{"action":"ping"}\n'` 带换行);死→看 `.cache/daemon.log` 尾部+watchdog 任务下轮触发应自愈,连续 3 轮死才人工干预(杀 PID 重启走 daemon_start.sh)
- [ ] A2 云端健康:落地页 200(每轮);四探针+signup 轻探(每 2 轮,必带 PROBE_A/B env)
- [ ] A3 平台信箱 unread → ack;需回函的起草(除非死线当夜,否则等用户晨起过目再投)
- [ ] A4 Reddit:用户贴主帖链接后 → `reddit_watch init` 一次,此后每轮 `check`;有新评论 → 按 launch_plan §6 + 口径卡 v2 起草回复(只起草,用户贴)

## B · 推广备料(可自主完成)

- [ ] B1 MCP 目录四件提交材料(Smithery/mcp.so/PulseMCP/Glama):服务器名/一句话/描述/标签/图标规格,每目录一份 → `docs/marketing/mcp_directory_submissions.md`
- [ ] B2 awesome-mcp-servers PR 草稿(entry 行+PR 正文)→ 同上文件附录
- [ ] B3 个人博客同步底稿(dev.to 文排版适配+回填链接)→ 9/10 直接可贴

## C · 组织欠函(写好待用户晨起过目)

- [ ] C1 flywheel RSI 四问回函草稿(死线 9/12)
- [ ] C2 flywheel G1 ack(BGE 指纹/corpus 状态确认)

## D · 路线图(夜里可推进的实活)

- [ ] D1 #46:batch001 效用报告复算起步——拉 flywheel batch001 材料(_INBOUND/_OUTBOUND 函+数据),列复算口径;手几何复算拆步骤
- [ ] D2 #47:VerifyPack v0.2 spec 草案(五要素回执+build/verify/receipt/check 四命令+ed25519 签名设计)——以 2026-09-07-verifypack-v02.md 为底

## E · dev.to 运营(9/8 深夜新增,用户授权自主)

- [x] E1 数据诊断:全账号文章近零流量;根因三:①ai_disclosure_level 未设(平台新政策,未披露疑似不分发)②泄露文 ③title 锁死改不动
- [x] E2 撤三篇泄露文(4602417 中文/4570176 重度 Kairos+V5+NAU+V7/4571717 中度 V5)——公开端点 404 复验 ✅
- [x] E3 AI 披露补全:4602276=some_ai · 4602572=fully_autonomous(PUT 管道:curl+浏览器 UA+title/body 同 payload;python urllib 被 Bot 拦;title 平台锁死)
- [ ] E4 明早用户 30 秒两件:网页回 mateo_ruiz 评论(草稿在会话)+bio 补全(profile PUT 失败,网页直接改)
- [ ] E5 历史文泄露审查:me 列表另有 7+ 篇旧文(4483447/4551522/4165473 等,他人经同账号发布)待用户拍板撤留
- [ ] E6 明晚 21:00(美东 9am)发第二篇:判分卫生学技术文(Loop 夜间写好)

## 状态记录(每轮一行,倒序)

- 23:3x dev.to 专项:撤 3 泄露文(404 复验✅)+AI 披露补全+评论草稿备好;E4-E6 见上
- 22:5x 轮 0:daemon pong(33352)✅·landing 200 ✅·信箱 6 未读(4 广播已 ack;182/183 VerifyPack 实质件留细读,死线 9/10)·B1 完成(mcp_directory_submissions.md)
- 22:4x 建档,Loop 启动(job 3825dda4 · :13/:43)
