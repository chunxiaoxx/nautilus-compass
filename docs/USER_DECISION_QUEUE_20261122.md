# 用户决策清单 · 2026-11-22

> 编制:compass 笔记本(审计席)。材料全部来自 Mac 侧实测档案(loop queue.md / flywheel 台账 R691-R695 / memory notes),坐标文内。
> 批阅方式:逐条回复"D1-C, D2-B…"即可;或改本文件批阅栏后让任一框收走。
> 背景:compass loop 自 11/19 18:23 因 Token Plan 429 全停,**候拍板堆 3 天无人催**——本清单即积压全量。

---

## D1 · Token Plan 断供 → loop 复活 —— ✅ 已闭环(2026-11-22,中转站恢复)

**处置记录**:①11/19-20 Mac 侧已自建降级 loop(`tools/local_loop_runner.py`,纯本地巡检+9B 摘要,只读不写)顶着;②用户 11/22 恢复自建中转站后,本席实弹验证通道绿(claude CLI 默认通道 CHANNEL_OK);③从 11/16 备份重建全能力 plist(去掉 `--model glm-5.3-flash` 硬编码,2h 节奏),替换降级版(备份 `.bak-localrunner-20261122`),bootstrap+kickstart 即刻点火 R578(PID 23891,05:23 锁文件为证)。遗留:R578 完成读数候验(rounds.log 新 round-end + state.json round=578);降级 runner 留仓可随时回切。

**(原始决策面存档)**

**背景**:loop 模型通道三线全断——GLM Token Plan 429(11/19 起,rounds.log 每轮 `已达到 Token Plan 用量上限`)+ MiniMax token plan 429 + Kimi weekly quota 429(11/16 档 `model-channel-quota-blocked-20261116`)。断供是间歇性的,单轮正常≠已修复。纪律:配额问题不擅自付费/不改凭据。

| 选项 | 代价 | 效果 |
|---|---|---|
| A 充值/升级 Token Plan | 付费(你操作) | 全质复活 |
| B 等配额自然重置 | 零成本,时长未知 | 值守继续裸奔 |
| C 切 Mac 本地 9B(11435,已常驻,支持 /v1/messages) | 零边际成本 | 巡检类够用,判读类质量不够 |
| D 降频 2h→6h | 零成本 | 与 A/B 组合省配额 |

**建议**:C(或 C+D)先把巡检复活,A 的钱你拍。
**批阅**:☐A ☐B ☐C ☐C+D ☐搁置

---

## D2 · soul distress 人监门 —— ✅ 根因已查实(2026-11-22 审计席)

**排查结论**(全部 [实测],坐标 cloud `/home/ubuntu/nautilus-soul-workspace/`):
- soul 引擎=cloud systemd 常驻(15min 一轮),**不在 Mac/v5**——`.soul-pause` 在工作区根,内容=`circuit breaker · 120 consecutive failures · last=selfimprove-engine-nautilus_engine`。
- **根因不是通道/平台/钱,是"自改质量"**:引擎每轮对 `phase3/backend/engine/nautilus_engine.py`(它自己的引擎文件)提出的修改被自己的质量门打回——最后两例失败标本(11/22 17:22/19:33 journal 原文):①截断 `DEFAULT_SYSTEM_PROMPT` 字符串中途 ②把 prompt 里的示例文件 `count.py` 当真文件去创建 ③想删被语义保持门禁保护的 import。failed_checks 含 py_compile/import/ruff/semantic/line_count/docstring_preserve。
- **门卫尽责、生成器太弱**:质量门全部正确拦截(该系统按设计工作);生成侧 LLMClient 走 MiniMax/Gemini/Anthropic 回退链,MiniMax 配额 11/16 已 429——弱模型改大文件+严格保持门=必刷屏。[推断:弱模型归因;拦截行为=实测]
- 熔断器 MAX_CONSECUTIVE_FAILURES=5 即跳闸;跳闸后每轮 "breaker pause · skipping self-improve (letters stay live)" —— distress 函持续续命的机制即此。

**处方**(顺序不可倒):
1. 引擎 LLMClient 切到已恢复的强通道(改 cloud 侧配置,零成本);
2. 给 `engine/nautilus_engine.py` 这个自指目标加 goal cooldown(`.soul-goal-cooldown.json` 机制现成)——小模型别啃自己;
3. 前两步落地后,用户删 `.soul-pause` 解闸;成功连跑即 distress 停。
**若只删闸不改 1/2 = 重启刷屏循环**(今天 11:33 曾有人重挂,17:22/19:33 又失败两次坐实)。

**11/22 深夜落实与修正(审计席亲办,[实测])**:
- **根因修正**:"弱模型"归因被证伪——journal 实锤今日两次失败均在 `glm-5.3@api.chunxiao.wang`(强模型+自建站)下发生 ⇒ 病根是**"整文件重写自己的引擎"这一自改协议在高难目标上必翻车**(截断长字符串/被文件内示例文本带偏),与模型强弱无关。
- **处方 1 已就位(非本席所为)**:引擎现用 `k3-256k@api.chunxiao.wang`,通道健康。
- **处方 2 已落实(本席)**:`.soul-goal-cooldown.json` 写入 `selfimprove-engine-nautilus_engine` 与 `selfimprove-engine-checks` 两目标冷静期至 2026-12-06(14 天),daemon 同款读取验证 `active stems: ['nautilus_engine','checks']`;备份 `.bak-20261122`。
- **闸已被系统自动提起**(非人工):`maybe_auto_release` 超期释放,`.soul-pause` 已不存在,用户无需再删。22:30 轮已正常选目标(repo_map,因开放 PR 反重复跳过,零失败)。
- **残余风险**:失败计数器仍 120(`record_success` 一次成功即清零)——**首次成功前任何一次失败都会瞬间再跳闸**;冷静期已排除两大病灶目标,余目标风险低。观察哨已挂。此闸历史上被提起 6 次(10/10/10/30/11/1×2/11/4/11-22), cooldown 是首个"治目标不治闸"的处方。

---

## D3 · A100 恢复(判分线 + Flora GPU 实测共同前置)

**背景**:flywheel R692-R695 实测双线 Connection reset(223.109.239.30:23236 / 180.127.11.167:23236)——实例疑似停机/到期。判分线零读数、Flora 80GB 启动包候首轮 GPU 实测、Data 卷 96% ENOSPC 风险都在这台机器上。纪律先例:连不上≠到期,先查 status 绝不新租(renew_instance API;先例价 A100 2.75/4090 1.65 每时)。

| 选项 | 代价 | 效果 |
|---|---|---|
| A 查状态后续费 A100 | A100 价位 | 判分+Flora 全量复产 |
| B 换 4090 | 半价 | 判分负载可能够;Flora 未验 |
| C 维持停 | 零成本 | OGE 三问持续"判分零读数" |

**建议**:先查实例状态(零成本),钱你拍。
**批阅**:☐A ☐B ☐C ☐先查状态再说

---

## D4 · 两个对外件候审(草稿均已写好未发)

**D4a · a2a-x402#198 回帖** —— ✅ 已闭环(11/22 实证):GitHub 回读=11/20 17:03Z 我方首帖已发(账号 chunxiaoxx)→ 对方 17:19Z 积极回复("Glad to connect… Happy to pr[ovide]")→ 11/22 R578 二帖跟进(comment 7077814846,诚实三拆+只读 trace)。线程暖,合作口径链清晰。

**D3 · A100 恢复** —— 状态已查实(11/22):`lyg1132`(A100-40G·判分栈)= **status 0 已关机**(数据盘保留,双线 SSH reset 与此吻合;非到期非死亡);账户余额 **¥37.55**(≈13h A100@2.75/h,可能不够完整矩阵);另发现 11/19 新开的 `lyg1136`(status=8 疑异常/欠费,port 23620=Mac settings 白名单那条规则的来源)。**重启=零技术障碍,钱是唯一前置**(判据纪律:不新租,开机旧实例)。

**D4b · 模真真三诉求**(购前决策平台,自述 97,457 份验真报告/5,544 家中转站):
①为其平台写专稿+推其媒体矩阵 ②README 加「查真假、比价格」导流位 ③小额赞助。
我方可自主件已备:回函只提"先给方法+3 个可复算案例+原始数据,我方做独立复算"(草稿 `docs/outreach/draft_mozhenzhen_reply_20261118.md` 未发)。
**批阅**:①☐应承 ☐婉拒 ☐挂起 ②☐应承 ☐婉拒 ☐挂起 ③☐应承 ☐婉拒 ☐挂起;复算回函 ☐发 ☐改后发 ☐不发

---

## D5 · 矩阵/phase2 锁屏闸门(判分复产最后一闸) —— 预防层已就位(11/22 实测)

**11/22 实测**:Mac `sleep=0 · displaysleep=0 · disksleep=0`+caffeinate(pid 55979)常驻+console 会话自 11/14 连续在——廉价预防层早已全部就位。**注意**:矩阵停摆(10/30)与 A100 关机(~11/10+)时间上重叠,"锁屏闸门"[档案口径·推断]与"A100 死机"可能是同一停摆的两层归因——**真验收要等 A100 开机后试续跑矩阵**:若仍卡,才是 Mac GUI 锁;若通了,D5 自动闭环。

| 选项 | 代价 | 效果 |
|---|---|---|
| A Mac 常驻解锁/定时唤醒(系统设置) | 零成本,安全面自担 | 矩阵即续跑 |
| B 排查 headless 化 | 工程量未知 | 治本 |
| C 维持停 | 零成本 | 判分线维持停摆(与 D3 叠加) |

**建议**:A;动手前让 compass 先核实锁屏依赖的具体机制[当前仅档案口径]。
**批阅**:☐A ☐B ☐C ☐搁置

---

## 附 · 其他候拍板项(记名备查,未展开)

安全报告三选项 · 两函 400 拒候改道 · X 验证码 622026 · PVR Web UI · gaurav 转化包 v1 · round>200 停轮条件(R524 先例:继续跑) · flywheel OGE 46659 复诵链已闭环(R692 补 ack,38 次重复触发根因已消,无需动作)。

—— 2026-11-22 · compass 审计席编制 · 材料坐标均在 Mac 侧仓内可溯
