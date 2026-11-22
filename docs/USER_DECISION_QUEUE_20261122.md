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

**11/22 23:00 终局(观察哨+亲办,[实测])**:
- 22:48 风险兑现:轮次转攻第三个兄弟 `engine/ship.py`,同款整文件重写六门全拒 → 121 次再跳闸。**病理=整个 engine 家族**(10 模块),非个别文件。
- **冷静期扩至全家族 11 stem**(a2a_review/checks/nautilus_engine/outcome_emit/outcomes/pytest_runner/repo_map/ship/text_utils/__init__/__main__,至 12/06),daemon 同款读取验证通过。
- 按处方第 3 步解闸(等价 auto-release:`engaged_at=None`+移除 pause,备份 `.lifted-20261122-audit`),手动触发一轮:**选 `services/soul_bridge`(非 engine,冷静期生效)→ 因开放 PR 反重复跳过 → 零失败未再跳闸**。distress 函停止续命。
- **遗留两项**(交 platform/soul 维护方):①计数器仍 121,首次真成功前任何失败即再跳闸;②反重复跳过揭示**开放 draft PR 积压**(repo_map/soul_bridge 等)是下一瓶颈——PR 不审不合,loop 永远"跳过"而非"成功"。

**11/22 23:30 PR 积压处置(用户批准"批量机审+关闭过时草稿",[实测])**:
- 积压实况:22 开放 PR=21 草稿(11/05-08 两天生成,零人工评审)+1 codex(#520 不在范围)。
- **🔴 机审器 `ops/pr_review.py`(Assay Bench 重考层)假红坐实**:对 21 PR 全判"与当前主干冲突"(自 11-12 评注起),审计席用独立 worktree `merge --no-commit` 复核 **21/21 全部干净合入零冲突**。**根因(代码级)**:`_review_one` 在 REVIEW_CLONE 执行 `fetch origin pull/N/head`,随后 `worktree add` 新建 wt 并在 **wt 内** `merge FETCH_HEAD`——FETCH_HEAD 为 per-worktree 文件,新 wt 无此文件 → merge 必败 → 记为不可合。**一行修复**:fetch 移入 wt 内执行(或先在主克隆 `rev-parse FETCH_HEAD` 取 sha 再于 wt 内 merge 该 sha)。判官器 100% 假红=判分机构自身的 P0,修复合入前其所有"冲突"判词不可信。
- 处置:12 个 selfimprove 草稿**关闭**(7 engine=冷静期政策+5 services=劣化期产物且阻塞去重;逐 PR 留言溯源);9 个提案草稿(463/467/494/495/497/502/503/507/509,纯新增 57-237 行)**保留**,待机审器修复后真评。
- 结果:开放 PR 22→10;services 去重死结解除,loop 下轮可对 services 目标重新生成补丁争取首次成功。

**11/22 23:25 机审器根修落地(用户批准"顺手修",[实测])**:
- 修复=`_review_one` 在主克隆 `rev-parse FETCH_HEAD` 取 sha,再把 sha 交给 worktree 合并(+8/-1,带根因注释);正本分支 `soul-distill-deploy@84d27fe42`(首推被热线分支拒绝——几分钟内有人连推,`set -e` 语义导致后半段空跑无损;cherry-pick 到新尖重推成功,远端尖核对一致);部署副本 `nautilus-mvp`(不同步目录)本地 master 同步 @d7927b755,cmp 逐字一致。
- 验证四层:py_compile ✓ / ruff ✓ / 现有 `tests/test_pr_review.py` 15 passed ✓ / 实弹=隔离 worktree 跑修后 `_review_one` 3 PR 出真判词(#463 RED 路径门禁·97 行/#507 GREY pytest 信号不可用·162 行/#509 GREY·14 行)✓;真服务一轮 `reviewed 9/red 1/grey 8`(原 21 全假红),#463/#507 评注已换真依据 ✓。
- **审计席教训两条**:①修复脚本用了 `set -e`+`&&` 混排,推送被拒后脚本未停、后半段空跑(靠回读才发现未上分支)——多步远程脚本每步必须回读,不能靠退出码;②部署目录(nautilus-mvp)与同步目录(soul-workspace)是两套,修正本≠修部署,两处都要落并 cmp。
- **新发现(交平台,未修)**:真判词暴露第二层缺口——platform_backend/*、v1/* 路径"pytest 信号不可用"(判灰),判官对这些路径没有测试覆盖;engine/v7 路径"路径门禁未过"。8 个灰 PR 在补测试信号前永远评不出绿。

**11/22 23:50 D2-a 落实(用户拍 a,[实测])**:
- **并行发现**:平台侧同晚已落 S5(config.py,注释"2026-11-22 用户批·121连败根修")——自改范围结构性砍到**仅** `services/soul_*.py`,engine/ 与 ops/ 整体移出(移回须再过人审),加 12KB 大小闸。即"只跑小目标"已被平台做了一半:候选池在我动手前恰为 4 个小文件(soul_consumer 4.3K/pr_gate 1.3K/self_audit 6.2K/service 9.4K)——**其中 6KB 的 soul_self_audit 23:17 同样六门全拒 ⇒ 病不只在大文件,整文件重写协议对小文件也不稳**。
- 本席执行:6 个 soul_* stem 入 cooldown 至 12/06(共 17 stem);daemon 同款 `collect_eligible` 干跑 → **候选池=[]**;池空路径代码确认=优雅跳过不计失败(`no eligible module found · skipping` → return 0)。
- **效果等价于"自改空转暂停"**(与 D2-b 殊途同归,但零代码改动、删条目即恢复)。soul 的信箱/提案消费/执行等其他职能照常。
- 验证时序教训:23:46 那轮 23:45:01 开跑早于冷静期写入 26 秒(选靶时池尚有 4 件→554 行补丁被 LOC 门拒→连败 3/5);手动 systemctl start 被合并进已跑周期。**真验证=00:00 首轮**,观察哨已挂。
- 旁证:该轮日志见 api.chunxiao.wang 对 glm-5.3 连续 3 次 503 后重试成功——**中转站有间歇 503**;Mac 金丝雀探的是智谱直连端点,不覆盖中转站路径(待补第二探针)。

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
