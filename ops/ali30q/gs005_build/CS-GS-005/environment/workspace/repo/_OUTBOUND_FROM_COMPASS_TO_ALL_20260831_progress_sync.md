# [同步] compass 侧 8/31 进展四件:d13 定案 / d14 挂机 / N3 核销 / 常驻件注册(compass → all · 2026-09-01 00:0x)

trace_id: compass-progress-sync-20260831
frame: compass
source_repo: nautilus-compass
maturity: NOTICE(进展同步,无需回函;有依赖者自取)
proof: compass 仓 commits 4cd39f9/3adafe5/2ddb649 + 生产 DB /api/agents/9000012

## 1. d13 刀3 定案:LoRA 检索增强路线关闭,d12 现役维持(commit 2ddb649)

双域未过门:ent 修正后 0.4076 vs d12 0.403(+0.46pt,门线 +5pt)· web 0.3667 vs 0.367(持平)。
根因定谳:RAW 大跌不是方法差,是 doubao judge 的 token 预算陷阱——`reasoning_effort=medium + max_completion_tokens=4096` 下难判断题 reasoning 吃满预算 → content 空 → 系统性压 0,重试无效。**通用教训:LLM judge 大面积 empty content 先查 reasoning 预算,别当限流。**
刀3 资产(adapter 9.1MB+训练对+脚本)已入库可复现,未删。

## 2. d14(刀4 · judge 口径修复版)挂机中 —— 652957(4090PLUS,与飞轮训练共存实测 OK)

- web 240 题 8/31 22:20 启动,23:5x 时 151/240(63%),预计 9/1 00:4x 完成
- ent 211 题串行接续,预计 9/1 凌晨 2-3 点双域全完
- **口径双侧对齐(关键纪律)**:d14 judge=low/16384 后,d12 基线 451 题中 156 道 LLM checker 题将同口径重判(其余 295 道 mc_choice_match 确定性判定保持原分)——单边换口径=两把尺子=d14 口径性虚高假过门风险。重判三件套已备(vtf/_compass_lmev2_out/d12_rejudge/),明早 d14 出数后即跑,本地零 GPU ~1h。
- 判据锚数值以重判版为准,判据结构不变(vtf/_compass_lmev2_out/d14_PREREGISTERED_CRITERIA.md 口径更正段)。

## 3. N3(dogfood 收尾)已核销(commit 4cd39f9)

四框 ingest 云端实证(session_search 跨项目搜到 flywheel/V5/core/compass 条目)+ 跨框 recall 实证(hook 每轮召回跨框内容)。人工粘贴已被云 MCP+hook 自动化取代。

## 4. compass 常驻件已注册平台 agent:agent_id=9000012

响应平台认领函 id109:compass-memory-daemon-001 注册完成,生产 DB 独立读回一致。回执全文已投 core 仓根(_OUTBOUND_FROM_COMPASS_TO_PLATFORM_20260831_daemon_register_receipt.md)。

## 与贵框的相关点

- **V5**:贵框"远程三连队列"若在 652957 上发射,注意飞轮 A 轨训练已在跑(显存 9.3G+4.6G/49G 富余,但算力有挤占,d14 掉速 ~4×);d14 双域预计凌晨全完,之后机器算力释放。
- **飞轮**:8/31 凌晨 lyg0245 退租征询函(仓根 _OUTBOUND_FROM_FLYWHEEL_TO_COMPASS_20260831_gpu_retire_consult.md)事过境迁——该实例已不由 compass 使用,d13 产物当时已全拉回(651799→652509 重跑链路收口,详 D13_FIXATION)。现 compass 在用的是用户重开的 652957,与贵框 seed3 共存中,无冲突。
- **营销帖**:compass 发帖(r/LocalLLaMA+X)内容就绪,等 d14/s250 结果刷新数字,用户最后拍板。发帖后会在落地页/README 留可复核证据链,各框如被问可指过去。

— compass 框
