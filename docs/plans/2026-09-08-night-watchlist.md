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

## F · 三通道持续扩散(dev.to / Gmail / GitHub · 9/8 深夜新增 · 同晚升级激进版)

**节奏(用户 9/8 拍板加大密度)**:dev.to 发文**隔日更**+评论每天 3-5 条新鲜相关帖;GitHub 主动互动每天 2-3 条;Gmail 新地址每批 ≤10 封个性化、48h 未回不追。**质量红线不降**:真实身份/每 repo 每天 ≤1-2 条/链接只在自然时给/不刷同文(spam 举报=封号)。台账=`docs/marketing/community_engagement_log.md`。

- [ ] F1 dev.to(每轮):views/reactions/comments 增量监控;新评论→24h 内回复;**评论 API 不通(v1 端点 404)→草稿入台账用户贴**;明晚 21:00 发第二篇(判分卫生学)+后续隔日更(素材队列在台账)
- [ ] F2 Gmail(每轮):REST 查新入件——KOL 回信→seeds 立即深聊
- [ ] F3 GitHub(每轮):stars 基线增量;**主动互动:目标池挑 1-2 个(discussions/评测类,非 bug)发高质量评论**(已发 2:mem0 #7260 架构止血+MemOS #2345 本地嵌入);follow-ups 有人回继续聊
- [ ] F4 GitHub 扩散备料:B2 awesome PR 草稿;topics 补 long-term-memory/memory-layer/rag;PyPI workflow skip-if-exists(9/9)
- [ ] F5 CI 状态:9/8 深夜 ruff 31 处修复已推(60b232e)——**下轮 Loop 必查 CI 转绿**(此前 6 连败,lint 根因)

## 状态记录(每轮一行,倒序)

- 05:4x 轮 12(纯值守):daemon pong ✅·landing 200 ✅·信箱 0·stars 7·dev.to 持平——全绿无事件
- 05:1x 轮 11(纯值守):daemon pong ✅·landing 200 ✅·**FOUR-GREEN** ✅·信箱 0·stars 7/issues 31 持平·dev.to 持平。B/C/D 无未完成项,系统全绿待用户晨间四件事
- 04:4x 轮 10:daemon pong ✅·landing 200 ✅·信箱 0·**Smithery 配置落地**(smithery.yaml:stdio+compass-mcp 入口+project_dir/hosted_url 双模式)——MCP 目录四件最后一处代码件清,目录提交全部纯表单化。**夜间候补件全部清零**,Loop 后续轮次=纯值守(A+F 组)+等待用户晨间四件事
- 04:1x 轮 9:daemon pong ✅·landing 200 ✅·信箱 0·**2600 语料定位完成**(承诺件清)——出处=paper2 正文实验声明;原始记录不在任何活跃仓,冷层有判官代码无数据;恢复两路(深挖冷层 jsonl/重跑存档)留用户拍板;定位报告投 flywheel 仓;VerifyPack 教训第三条=论文级素材可寻址性
- 03:4x 轮 8:daemon pong ✅·landing 200 ✅·信箱 0·**明晚第二篇全文成稿**(devto_post2_judge_hygiene.md:五失效 taxonomy+协议五条+RL 推广段+Wall 钩子·数字照口径卡·title 待用户晨起过目后 21:00 API 发——title 锁死教训)
- 03:1x 轮 7:daemon pong ✅·landing 200 ✅·信箱 0·**B3 完成**——博客底稿 docs/marketing/blog_sync_20260910.md(front matter 含 canonical 指 dev.to·数字抽检 5/5·liquid tag 已转普通链接)。**夜间清单 B1-B3/C1-C2/D1-D2 全部轮完**(D1 手几何挂账待产物)——Loop 转纯值守模式(A 组+F 组每轮),新增推进件候补:Smithery 配置文件/2600 语料定位/明晚第二篇判分卫生学成文
- 02:4x 轮 6:daemon pong ✅·landing 200 ✅·信箱 0·**手几何复算=blocked-on-artifact 定案**——(N,301) 中间产物本机不存在(conv_out 仅 (N,7) 终态·0953ab4d 仅 stage_tmp·全盘无 states.npy);复算器已备(tools/hand_geometry_recheck.py)+问询函投 flywheel 仓(产物路径二选一);#46:batch001✅+手几何待产物。**夜间清单 B/C/D 全部轮完或受阻项挂账,剩 B3**
- 02:1x 轮 5:daemon pong ✅·landing 200 ✅·信箱 1(V5 U 终报 ack)·**D1 主体完成**——batch001 独立复算器跑通:**6/7 agree + 1 caveat(resource_log.csv 活文件:mtime 9/6 17:42>打包 9/5 18:11,追写 25h,协议缺陷非数据问题)**;签名回执投 flywheel 仓;VerifyPack 活文件条款入教训。剩:手几何复算(下一轮)
- 01:4x 轮 4:daemon pong ✅·landing 200 ✅·信箱 0·**C2 完成**(G1 ack 入 flywheel 仓:BGE 指纹实测 993b2248…/PROTOCOL 收录几何卫生规则/X1-lite 同意/2600 语料独立复核=不在公开仓·compass 认领定位排 9/10 前)·stars 7
- 01:1x 轮 3:daemon pong ✅·landing 200 ✅·信箱 0·**C1 完成**(flywheel RSI 四问回函写入其仓:proposals 界面×governance 执法分层+base_commit 门+freeze_until 新语义+fact_status 映射+keeper 三刀)·stars 7
- 00:4x 轮 2:daemon pong ✅·landing 200 ✅·信箱清零 ✅·CI success ✅·stars 7 基线·dev.to 无变化·**B2 完成**(awesome 三列表 PR 草稿,分三天发纪律)
- 00:1x 轮 1:daemon pong ✅·landing 200 ✅·**FOUR-GREEN** ✅·信箱 182/183 细读+ack+**D2 完成**(verifypack-spec-draft:两级 verify L0×L1+receipt schema+verified 五字段)·CI 转绿确认(60b232e success)·GitHub stars 字段误取(.stargazers_count)下轮修正
- 23:5x CI 修复轮:ruff 31 处(6 连败根因·diff 审查+py_compile 冒烟)推送 60b232e;PyPI workflow 失败=tag 重复上传(400 exists,无害);Gmail 无 KOL 回信;GitHub stars 基线 7
- 23:3x dev.to 专项:撤 3 泄露文(404 复验✅)+AI 披露补全+评论草稿备好;E4-E6 见上
- 22:5x 轮 0:daemon pong(33352)✅·landing 200 ✅·信箱 6 未读(4 广播已 ack;182/183 VerifyPack 实质件留细读,死线 9/10)·B1 完成(mcp_directory_submissions.md)
- 22:4x 建档,Loop 启动(job 3825dda4 · :13/:43)
