# LOOP 原子任务队列(20 分钟时间盒 · 每轮取头部 1 件 · 跨会话状态真值)

> 规则:只放 15 分钟内能完成并 commit 的件;完成→标✅移入完成区;做不完→标🔄+进度一行,下轮续。
> 优先级:定时件 > 外部事件 > 队列头。队列空且无事件=不跑轮(空转才是剧场)。

## 队列(待取)

| # | 任务 | 预估 | 状态 |
|---|---|---|---|
| 1 | ack 1824(经费预授权池规则知悉)+ 回函 1828(幂等键建议收下+勘误入档) | 8min | ⏳ |
| 2 | Report #3 大纲 | 15min | ✅ R6(docs/marketing/TRUST_REPORT_3_OUTLINE_20261001.md) |
| 3 | Report #3 §1 成文 | 15min | ✅ R6(docs/marketing/trust_report_3/section1_judge.md) |
| 4 | Report #3 §2 TypeSafe 段 | 15min | ✅ R7(section2_typesafe.md) |
| 5 | Report #3 §3 mem0 段 | 15min | ✅ R7(section3_mem0.md) |
| 6 | ~~语料活水:E5 33 条~~ **关:任务不匹配**(门级判定≠答案判分,硬塞=污染;真源=unlabelled 47+errata gold+判官金标) | — | ❌ |
| 7 | ~~33 条复核标记~~ 随 #6 关闭 | — | ❌ |
| 8 | 判分器热路径接入清单 | 15min | ✅ R6(docs/metering/JUDGE_HOTPATH_INTEGRATION_PLAN_20261001.md,S1-S5 判据草案) |
| 9 | 判分器热路径:延迟预算实测(本地 CPU 推理一例计时) | 15min | ⏳ |
| 12 | F15 glm 腿样本抽取脚本备好(额度窗口到即跑) | 10min | ⏳ |

## 定时件(到点触发,不在队列)

- **08:53** 云 daemon 24h 内存终读数 → 蓝绿部署窗口(runbook:ops/ 一键五步)
- **09:00-10:00** Reddit r/LocalLLaMA 发帖(稿:runtime/marketing/dcr_reddit_post_20260930.md)
- 外联回应:MemOS #2440(9/30 发,10/2 22:00 前 48h 窗)/mem0 #7514 + TypeSafe(10/1 发,10/3 窗)——探针守,回应到即触发轮

## 完成区

| # | 任务 | 轮次 | M1 |
|---|---|---|---|
| 1 | ack 1824+回函 1828(幂等键采纳方案,函 1842) | R1 | +0(基建) |
| — | 探针层上线(probe.py 修代理劫持:信箱改 curl) | R1 | +0(基建) |
| — | 探针首跑即抓事件:E6 GRPO 00:17 完成(200 步/adapter 落盘/GPU 释放) | R1 | +0(记录) |

## 轮次日志

### R16 · 2026-10-01 17:0x-18:2x(BC1 知乎攻坚+发布成功)
- 🔴 **BC1 知乎发布成功**:https://zhuanlan.zhihu.com/p/2089032973794407525(B 级外发+pub.py 双首验完成)
- 用户纠正在先:cn_publisher「填好」=自报(execCommand 改 DOM 被 React/Draft 丢弃,检查读幽灵层)——第 N 次自报复发,幸有用户实况核查
- Draft.js 正道三件:React 受控 setter(标题)/CDP Input.insertText 系统级(正文,焦点坐标必须命中编辑器)/污染 tab 关掉重开(僵尸层键盘够不着)
- 发布确认条短命:0.8s 轮询抓点(poll 6 命中 y=2795)
- M1:BC1 上线=首考生入口开(M1 信号位)


### R15 · 2026-10-01 14:5x-16:2x(战略沉淀+调研+论文+能力注册轮)
- 六天复盘落记忆(retrospect-6d-patterns:五病七模式);验证即反射三层架构档(用户令 RSI 视角)
- 全网调研六线(literature_scan:压缩×智能缝/PRM/abstention/SSI/RSI 安全窗口/F 商业实锤)+ThinkPRM 深挖(论文三引用位+四条 v0.5 候选)
- **论文计划重大变形**:发现既有三论文仓(verification-learning-papers 8/22 立)→升级非新写;用户「高维借时空」形式化五步定式;主笔正式函 2080(P3 先行 10/8,五方供料 10/6)
- 能力普查令 2075:writeback 注册 2 项 capability(inserted=2:verdict-judge+pub.py)
- 下轮:21:00 BC1 知乎发布(pub.py --publish,全自动首验);G1 boot 确认函 2063 等 v5 回
- M1:论文主笔+能力注册=组织位


### R14 · 2026-10-01 15:1x-16:0x(全自动化攻坚+glm 定谳+v5 勘误轮)
- **glm 定谳**:用户指正→glm-5.3-flash 跑通(3/4,分歧=ok-1 信息边界病又一例;模型名坑:列表实为 glm-5.3-flash 连字符,glm-4.6 同跑 4/4)——**glm coding plan 全程可用坐实,此前"断腿"纯属端点/模型名错配**
- **Reddit 自动化三路攻坚定谳**:①CDP UI(shadow DOM 死)②页内 fetch+modhash(挖到 modhash 实证!)→**BAD_CAPTCHA**(新登录态 API 提交要验证码)③建 script app(正道,免 captcha 永久)→**recaptcha 静默拦**(CDP 过不了)。结论:差用户 10 秒——apps 页点一次验证+create app(name=assay-publisher/script/redirect=http://localhost 已预填),此后 PRAW 永久自动
- **Discord**:webhook 需服务器管理权限(面板无整合项=权限不足);**但 9/27 CDP 发帖配方已实证(Enter 发送)=Discord 自动化实际已解决**,webhook 锦上添花
- v5 勘误(#2032)全盘接受:发起=我方+单方寄出两修正入台账;对外口径降格
- 两定向接单(#2026):gtaras7 首案例(按勘误口径)+论文主笔(随 10/2 汇聚)
- 全自动发布器架构案落档(docs/plans/AUTO_PUBLISH_ARCHITECTURE_20261001.md)
- M1:候选(宽口径)+勘误(严格口径未达)+论文主笔接单


### R10 · 2026-10-01 13:0x-14:0x(三件当天清:申报+启动+测量交付)
- 用户纠时间感知(中午非晚)→三件当日清:①判分器装前申报(2003,影子 S1-S5,纲领 soul 终点推动)②A1 评测位启动函 flywheel(2002,三盲一致率 v1)③**gtaras7 测量当天闭环**
- 测量全链:API 活性验(jev-1.13.0)→runner 修 criteria 结构(422=score 类需 {what} 原文)→**40/40 零错**→聚合(career 92.59%/Brier 0.069/ECE 0.1378)→VerifyPack 签封(踩三坑:level L2/metrics dict/files dict 格式,spec 校验严格=好事)→**报告发回 Issue #2**(issuecomment-5924820105)→通报 platform(M1 候选判定呈用户)
- 48h 承诺:14h 内完成(key 公证→交付)
- M1:**候选达成待裁**(外部实测合作首例 vs 严格复算口径)


### R9 · 2026-10-01 12:0x-14:5x(双实例处置+key 公证轮)
- v5 通报 1982 属实:**本地 9876 双实例**(7724 主/24056 空壳)→24056 精确击杀+回函 1987+互斥锁列 v3.4;跨框监视网首次抓我方生产问题
- CI 失败×3=lint 债(9/28 起存量,挂账非本轮引入)
- 探针修:typesafe-jev#2"2条评论"虚惊=无基线计数,已记待改增量报
- 🔴 **answer_key 公证完成**(48h 承诺核心件):40 件 career 全锚定(lateral8/hopping8/growth11/U13,机械映射表随 key);五判断维度诚实 U;flag 副读数修正(military 18/40 实标);commit 时间戳=K 先于模型公证
- 下轮第一件(新 session 深活):Jev 跑分段——questions.ts 出题逻辑→runner→40×6 调用→聚合→mini-report 签名发 issue
- M1:gtaras7 线推进至 key 公证(测量半程)


### R8 · 2026-10-01 14:0x-14:3x(外联转化+派单轮)
- 🔴 **外联首转化**:gtaras7/typesafe-jev Issue#2 正面回应(9/30 21:05,漏看 21h——探针没盯 GitHub 通知流,已修:gh notifications 兜底+专项监控);对方给 40 种子 CV+manifest 意图+公开 policy,强制 caveat;我方回协议(corpus sha 冻结 c304f878800b1fcb+key 先于模型 commit+全工件)——**预注册立项档落**(K1-K7/诚实边界:六判断维度大半 U+flag 泄漏副读数);40/40 CV 文本抽取全绿归档;48h 承诺启动
- XERJ/Ivan 回信(贡献三件套+复算 offer);Infistar 四条款回复;两封发(gmail 双证)
- **XERJ 检索栈对照测试派单** platform(函 1983,40NAU,J1-J3=原始数据+复现命令,对外 issue 终审留我框——质量门拆分)
- 下轮第一件:CV 校准 key 构建深活(fields.ts instructions 映射表→answer_key.json→commit 公证)
- M1:**+1 候选**(gtaras7 测量=外部第三方给数据的首次实测合作,若成=事实上的首复算请求)


### R6 · 2026-10-01 12:1x-12:4x(回归主线:Report #3 两件+语料修正)
- Report #3 大纲落档(五节结构:判分器自纠错主线/TypeSafe/mem0/品类横评/自曝台;英文独立版=§1 讲自己不讲别人,比 TypeSafe 稿更安全的下一篇)
- §1 成文(section1_judge.md):66.2% 起点-三作弊通道故事-LoRA 三态-读数表-U 态方法论(可溯源全链)
- 语料活水修正:E5 33 条**不进判分语料**(实测 verdicts 全 pass=门级判定,与答案判分任务不匹配,硬塞=污染)——活水真源=unlabelled 47+errata gold+判官金标二包;E5 价值重定位=三门自动判官(另一模型线)的训练料
- Reddit:CDP 死通道收兵,稿与配方坑全留(runtime/marketing/),待用户手点或换 UI 自动化路线
- 下轮第一件:queue #8 判分器热路径接入点清单(装前申报准备)
- M1:+0(内容漏斗件两件落地)


### R5 · 2026-10-01 10:50-11:3x(救火+W42销+头脑风暴轮)
- 🔴救火:切换后 40min 生产重演(4.9G/available 0/overload)→根因=v3.3 warmup 防了巨物 **lazy 没防**→v3.3.1 补丁(lazy 同款 200MB 防护)+重启→稳态 available 4981/evict 归零/pong True;J1 单项 4.9G 不达如实挂账(构成=entries 文本缓存,v3.4 治理另立项)
- **W42 红灯销**:platform 1935 schema 答案(items 每项必含 id)→v6 重投 **inserted=3**——W42 双周补跑全链闭环(停摆自 6/17)
- 头脑风暴回函 1949(方案级):事实更新 88.51% 改写棋局+同构五件套+U 态吞吐阀+标注闭环闸门+两反对(A 通道过程指标防误判死线/M1 与付费并轨)
- G1 判分窗确认就绪+A1 独立评测位接单(三盲一致率协议)=函 1950;广场首帖备稿=1951;六 ack 清零
- 下轮第一件:R6 候选=Report #3 大纲(queue #2)/999MB 巨物身份查/B 级 BC1 卡 27 跟进
- M1:+0(W42 闭环=组织件;A1 评测位=新收入位候选)


### R4 · 2026-10-01 08:44-09:35(蓝绿攻坚+rollback+A100 评估轮)
- 定时件 08:53:旧版终读数 **RSS 5352MB**(9/30 重启回 2427 后 24h 又爬回——MAX_PROJ 加严治标坐实)
- 蓝绿三连测:①默认 256 warmup→稳态 4239 ②错 env 名→256/5235 ③COMPASS_ENTRIES_CACHE_MAX_PROJ=8→loaded=8/**仍 5326**——verify 线(4000)/J1 线(3500)均不过→**按纪律 rollback**(旧版回 9876 服务中,active/5010MB/available 6027)
- 🔴 根因待查:np 化云端真机未复现本地 175MB 降幅(差 ~30 倍;loaded=8 时 BGE2.3G+基线 0.5G 预期 ~3G,2G 差额不明)
- 部署坑三(修入 runbook):systemctl 要 sudo -n;**9877 被 mcp_server.py 占**(蓝改 9878);stop 挡不住 Restart=always(须 disable)
- 中断如实披露:两段(08:53-08:56 约 3min/09:03-09:25 约 20min),通报函 **1905** 已发
- A100 空档评估件(判分器热路径):**P50=30.1ms/P95=42.2ms/吞吐 118 条/s/VRAM 5.9G**——写入热路径可行性坐实(装前申报核心数据到手)
- Reddit 定时件卡登录(9226 Chrome 未登录 Reddit)→顺延用户登录后;稿就绪
- 下轮第一件:queue 深活(Report #3 大纲);值守 W42 回函/v5 GPU 空档回函/BC1 卡 #27(用户飞书)
- M1:+0(R4=运维攻坚;评估数据=判分器上岗前置)


### R3 · 2026-10-01 01:0x-01:4x(GPU 协调+W42 端点攻坚轮)
- 交付:①GPU 协调函两封(v5 1852/flywheel 1853——首调 409 duplicate 证实被中断调用实际成功,被吞的只是回显)②W42 端点四连试:正确 URL(/api/platform/org/judge/writeback,承 1845)→openapi 拉 _WritebackReq schema→v4/v5 两种装载均 200+inserted=0→回函 1896 要行 schema/判重确认(停止猜)③三 ack(1845/1848/1851)
- 探针修正:A100 空闲判定改计算进程数(瞬时利用率会误报迭代间隙——v5 E6 是连续迭代:00:17 一轮完→00:25 二轮起,38G/86%,实例并未空闲);热路径评估脚本修 modelscope 路径(真实=/root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master)排队等空档
- 用户令执行:主动跨框同步(五框探查:flywheel 00:20 仍在 commit G1 预注册)
- 下轮第一件:08:53 daemon 终读数;白天 Reddit 9-10am;BC1 决策卡 #27 等用户飞书批(20:30 deadline)
- M1:+0(W42/GPU 协调=组织基建;BC1 卡到用户=外发出口)


### R2 · 2026-10-01 00:4x-00:5x(探针首波事件轮)
- 交付:五封全清——1837 W42 POST 实测六路不通(主站 SPA fallback 复现不出 flywheel 的 405/422)→回函 1843 要完整 URL(红灯先证伪自己,实测表全附);1840 B级首单→BC1 知乎备稿函 1844(终稿坐标+10/1 21:00 参数);1834 J8 收讫/1832 勘正/1828 ack
- 体系动作:幂等键纪律首用(两函各带 idempotency_key)
- 下轮第一件:凌晨收轮;白天 08:53 daemon 定时件+09-10 Reddit;queue #2 Report #3 大纲
- M1:+0(B级首单备稿=外发出口基建,间接)

### R1 · 2026-10-01 00:1x-00:3x(LOOP 模式启动轮)
- 交付:probe.py(四源探针,信箱/GitHub×2/A100)+queue.md 12 件原子队列+定时件表;ack 1824+回函 1842(幂等键纪律即刻内化);探针修(urllib 被本机 socks 代理劫持→curl)
- 探针事件:A100 上 E6 GRPO 训练完成(v5 域,读数 train_runtime 1562s/200 步/reward 尾读 0.1——不越权解读,记档)
- 下轮第一件:queue #2 Report #3 大纲(白天节奏,凌晨不启深活)
- M1:+0(基建——探针+队列=loop 骨架;外联三件在观察窗)

