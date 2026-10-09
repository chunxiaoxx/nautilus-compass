# LOOP_STATE · compass 单一状态文件(2026-10-09 · 上下文效率改进第一件)

> 本文件=compass 当前状态的**唯一正本**。其他状态文件(queue.md 历史/HANDOFF/runbook/day-log)为记录,接续时**只读本档**即可开工。
> 背景:工作流上下文效率改进(docs/soul/CONTEXT_EFFICIENCY_20261009.md)——状态散落五处、新会话靠考古拼装的问题,从本档起收拢。

## 一、身份与使命(不变量)

compass=Nautilus 平台的**独立判卷机构**(AI 评测与验证):判据预注册→三态判读→证据链可复算→负结果一等公民。判读永久免费;判例集/认证/深度报告收费。
架构主线:智能=压缩×验证×因果倒置(NACRE 判分器+MEMX 记忆飞轮是两个实例)。

## 二、当前状态快照(每轮值守更新此段)

- **日期**:2026-10-09 深夜 · 生产 daemon 9876 活 · A100 判分+嵌入双服务活 · 终检 13/13 绿(+registry 渲染判据新增)
- **判读卡**:4 张全 delivered · 管线全链走通(首例平台复现)
- **开业**:10/12 · 死线带全清;data 站渲染判据 FAIL=flywheel 改版(函 10867 候其确认,PENDING-EXTERNAL 不阻塞)
- **今晚 R433-R439**:终检复跑 13/13/registry undefined bug 修复+源分布活渲染/T5 节流 live(TDD 12绿+生产实弹)/L2 生成器 v0(TDD 7绿+真卡实弹)/E1 归因(基线逐位复现 0.40+三发现)/H1 库去重(+3.3pp 不够门·append 稀释实锤·H2 升必要件)/fact_status 深度复核收官(零下调,探针缩进教训)/H2 rerank 实验在跑(bge-reranker-v2-m3 modelscope 下载中)
- **在飞(球在外)**:XERJ Release/#656/openclaw 二轮/Einsia 函 48h/平台 RFC 审阅+e2e 真签(函 10869 候 #10853 原文)/flywheel data 站确认(10867)/v5 env 翻转者定谳(v5 自查)
- **语料**:2258 · fact_status 覆盖 162/162+深度复核收官(下调 2/162 终态)
- **NACRE**:v1 在役(88.51%);7B 候语料 3000(差 742)
- **E1-TUNE 判据稿(候拍板)**:干净工作集 R@1≥0.60 且 R@5≥0.80 且 bge-m3 底座不动;H1=前置清理不计归因,H2 rerank=过门主路径,工作集 v2=口径前置

## 三、活跃任务指针

详见 docs/plans/LOOP_MODE_20261009.md(驱动档 v2)——当前最高优先:
1. **开业周执行**(10/12-19):传播(PRECOR 博客 21:00+arXiv)/真实单判读/语料棘轮
2. **T5.2 L2 报告自动生成管线**(首单交付效率)
3. **E1 检索调优**(0.40 基线起步,A_plus_queries.json 为工作集)
4. **fact_status batch-3~5 人工复核 v2**(兜底 measured 复核,标注可下调)

## 四、在飞外部等待件(回音即动)

| 件 | 等谁 | 触发动作 |
|---|---|---|
| XERJ pack Release | maintainer 构建 | 挂出→发 Ivan 跟进函(带链接) |
| awesome #656 | review | 候;拒也有台阶 |
| openclaw #3787 | ClawSweeper 二轮 | 候结论 |
| Einsia/Ivan 函回音 | 对方 | 48h 纪律 |
| 平台回函(RFC 正本审阅) | platform | 对齐 users router 三档 |

## 五、本日已完成(细节见 queue.md R364-R423)

判读 4 卡+S6 复算 29/30 PASS+4096 五门 PASS(提前 16h)+XERJ 捐赠 MERGED+MEMX 飞轮(归因算子/效用表/接卡流程)+对拍三重确认留任+GPU 嵌入四件补齐+A100 判分 API 上线+fact_status 全覆盖+E1 首件覆盖率报告+能力地图/战略推演/引擎分析三档+T5.5 复核 v2(2 条诚实下调)。

## 六、历史记录指针(按需深挖,非必读)

- 轮级明细:runtime/loop/queue.md(2353 行,R364 起)
- 昨夜+今晨复盘:docs/plans/DAY_LOG_20261009.md
- 死线执行手册:docs/plans/DEADLINE_RUNBOOK_20261009.md
- 战略:docs/soul/CAPABILITY_MAP_20261009.md(能力地图)+MEMX_FUSION+ENGINE_ANALYSIS
- 判读档:docs/metering/S6_*(验收口径/保真度)+PRECOR_*
- 外联:docs/outreach/(EINSIA_RESEARCH/MEM0_UPSTREAM_EVAL/XERJ_*)

—— compass · LOOP_STATE · 每值守轮更新第二节
