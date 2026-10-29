# nautilus-compass · 项目指令

> 🔴 **判断前三查(10/29 事故机制·永久强制)**:①答甲方/组织问题前→查反馈台账(nautilus-core/docs/ALI_FEEDBACK_LEDGER_V1.md)已答清单,已答勿再问;②判读/判状态前→查正本(nautilus-core/docs/feishu/ 两原文+标准全图V1)原文行号,禁用转述;③自报零采信→一切"已完成"以实物抽验为准。阿里判据五条件+正本坐标见本框memory ali-criteria-v11。

> 🔴 开工第一动作(frame-upgrade-20260904-compass #2 · MetaGPT _observe 原则;10/19 F1 bootstrap一口):先取组织态再开始其他任何事(10/19 F1 升级 bootstrap 一口)——`curl -s "https://nautilus.social/api/platform/org/bootstrap?agent=compass"`(registry/未读函/goals/health 一口)→ 逐封 ack(需正文回函的按 trace 回函),然后才开工。本框状态自报见 `FRAME.yaml`(状态变化时顺手改)。

> 🔴 方向锚(2026-10-29 更新,与仓内任何文档冲突时以此为准):
> **当前业务 = 阿里 CodeSense 出题生产(14 题·周五交付)** + 判据工程化(gate5 七门) + 验证机构(CASSAY/JEV/VerifyPack)。
> 旧方向锚(具身智能/垂域出题已死)已被 10/25 阿里委托取代——仓内 FDE/CHARTER/SSOT 为历史层,考古时手动读,读时牢记历史层 ≠ 现状。
> **compass 分工(22905 平台裁定)**:判据工程化(gate5)+独立判读卡+判分值守。**不做**:出题、调档设计(判据独立防自评)。
> **素材化路线(23249 用户拍板)**:出题用真实仓代码·spec 无素材卡号不受理·验收四判据钉死(载体真实/坑真实/>300文件/UT锚badpattern)。

> 🔴 判据正本(2026-10-28 取回,之前全部按转述生产=结构性偏差):
> 需求文档 = `nautilus-core/docs/feishu/需求文档_题目结构与跑分结果.md`(1145行)·质检方案 = `nautilus-core/docs/feishu/质检方案_题目质量细节.md`(1677行)
> **判据五条件**(质检方案行525/527): 五模型各4轮·整体全对率<70%·opus全过轮∈[1,3]·qwen双低且≥1轮零分·qwen passrate∈{25%,50%}
> **判据 v3 基线** = `runtime/pipeline_state/criteria_v2_baseline.json` + `criteria_lock.json`(sha16冻结)·校准协议 = `calibration_protocol_v1.md`
> **gate5 判定器** = `ops/ali30q/gate5.py`(七门·构造校验通过)·**预筛器** = `ops/ali30q/opus_prescreen.py`

> 🔴 报数纪律(2026-09-15 用户拍板,流程正本 `docs/soul/proposal_preregistered_recompute_20260914.md`,soul 提案 approved):
> 对外要报数字的任务(评测/跑分/数据产出/修复验收)——**开工先落预注册判据档**(判据只许更严),**收工走非实现者复算**(新鲜会话,只信判据与自测);交接档只给坐标与命令,**不给任何预期读数**(占位句也不写,留空白)。复算红灯先证伪自己探针。
> **判分证据分层(2026-10-03 用户拍板,正本 `docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md`)**:判分/复算/验收报告的每条结论性陈述必须标注 `[实测]/[推断]/[不可验]` 三层之一,推断不得冒充实测,推断发布即带 upgrade_path,U 态与证据层独立标注。

> 🔴 生产纪律(10/28 全天教训汇总):
> - **开工预检 gate0(10/29 新增·强制)**: 出题/判分/打包前必跑 `python3 ops/ali30q/verify_criteria_lock.py`——判据锁八件 sha16 校验,FAIL 即拒开(判据只许更严,变更须新版本锁重发)
> - **判据原文未取回前不出题**(零达标第一根因·9 月即已发生)
> - **passrate = 整题全对率**(全对记1否则0·行758),非 UT 通过率
> - **opus 方差带选题法**: opus 全过轮∉[1,3] 的题不投——预筛器 2 轮快测定落点
> - **/tmp 会周期性全灭**: 生产件一律放持久路径(`runtime/scratch_*`),不放 /tmp
> - **身份字符串 ≠ 机器位置**: 判断来源只看文件系统坐标,不看 agent 名
> - **passrate 梯度 ≥15pp + qwen∈{25,50} + opus∈[1,3] + 整体<70%**: 四条联合达标才有区分度
> - **Harbor 1.4 结构条款(§3.1-§3.10)**: calibration=patch格式(非json)·编号CS-<供应商代号>-<序号>·Golden/NOP双向预检

> 🔴 MCP 配置(2026-10-27 定型):
> - 项目级 `.mcp.json` = 本地 stdio(venv python + PYTHONPATH 仓根)·服务 8097 launchd 常驻+watchdog 5min 自愈
> - user 级 `~/.claude.json` = http://127.0.0.1:8097/mcp/(笔记本/cloud 侧 agent 经 Tailscale 100.84.23.45:8097/mcp/)
> - token 文件 `~/.claude/.cache/compass_mcp_tokens.json`(0600·20 token 合并)·**改 token 必须 kickstart 重启服务**

> 🔴 循环(7 层·全 launchd 常驻):
> bait-loop(120min·glm-5.3-flash)·compass-loop(30min·含管道刷新)·pipeline-sync(30min)·mcp-watchdog(5min)·s5_receiver(watch)·判分矩阵(每时轮)·compass-daemon(9876)

> 🔴 值守报表新增(23249): 每轮加一行"素材主线: 卡N/题N/门N"·连续2轮零进度自动亮牌

<!-- COMPASS-KG-NODE · 2026-07-14 从 4 个历史会话提炼 · 完整见 ~/.claude/projects/<proj>/memory/session_NODE_nautilus-compass.md -->
## 📍 项目现状与复发陷阱(compass 记忆提炼)
本项目 4 段历史已提炼进 compass memory,开工用 `recall` 召回相关条目。复发陷阱速览:

- 自报不算,能独立复现才算(项目立身之本,连自家README也是'自报')。
- 探针/结论红灯先证伪自己,别默认被测物有病(去伪比抓病更高频有效)。
- 件数≠价值 / 活着≠可观测≠有产出(剧场识别核心尺子)。
- 改动前先 grep 仓库找旧实物(标准MCP/DB连接配方/探针都曾被重造);SSOT drift=精神分裂病根。
- **立项先问材料本体**(10/19 自举线定谳,勘误档 §四-3):攒语料/造数据集前先回答"这材料对人类专家有无客观对错"——没有就只能做检索/无监督,做不了监督训练燃料;数量里程碑(3000/4002 达标)在无外部真值校验时一律不算进展。
- **重启旧线先查前次终止原因**(10/20 对账新增,勘误档 §四-5 / EFFORT_ACCOUNTING_20261020):复活任何已停线/过期线前,必先找到该线上一次的终止记录与原因并对照"原因是否已消除"——8 月燃料原型当年自然过期,10 月重启无一处引鉴,教训未入 checklist 是再发条件。
<!-- /COMPASS-KG-NODE -->
