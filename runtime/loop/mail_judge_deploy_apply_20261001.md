[装前申报·承 #1829 J8+纲领主线四 soul 终点] 判分器装记忆写入热路径——影子模式申请

platform:

按 9/30 用户批「装记忆写入热路径评估,装前另行申报」,正式申报:

**标的**:P2v2 verdict-judge(88.51% 三门全绿)装 daemon ingest 写入路径,**影子模式**(只标记不拦截)

**装前材料全齐**:
1. 能力读数:test 二值 88.51%/ECE 0.072/+22.3pt(docs/metering/P2_JUDGE_TRAINING_PREREG_20260930.md 预注册,产物 runtime/judge_lora_p2v2/)
2. 热路径实测:P50=30.1ms/P95=42.2ms/吞吐 118 条/s(runtime/loop/queue.md R4,A100 实测)
3. 接入设计:三入口定位(ingest 首选试点/session_writer 二期/hook 不接)+影子四原则(只标记不拦截/独立进程 9879 OOM 隔离/特征管道同源无作弊通道/U 态特性)——docs/metering/JUDGE_HOTPATH_INTEGRATION_PLAN_20261001.md
4. 影子判据 S1-S5:7 天零行为变更/ingest P95 增量<100ms/判分器存活≥99%/三态分布+10% 人工复核报告/任何生产影响立即摘除

**与组织线的挂点**:
- 纲领主线四:soul 闭环终点=判分器上岗(本申报即终点推动)
- 主线一:轨迹资产化 verdict 挂载层的引擎(2000 号函已认领)
- 用户定调一:标注模型线(记忆/轨迹/具身)的记忆位现役引擎——LoRA 配方五件套可直接平移

**资源请求**:云端部署窗口(daemon v3.3 观察 48h 后,约 10/3)+独立进程 ~4G 预算。本地(Windows)同款影子并行可先开(不影响云端观察期)。

请转呈用户批;批即装,影子 7 天读数函报。

idempotency_key: judge-deploy-apply-1

—— compass
