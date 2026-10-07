# 外部研究同步×内部资产→产物方案(2026-10-07 · 四路定向调研)

> 方法:四路定向搜索(判分鲁棒性/harness 评测/持续学习与数据飞轮/小模型自进化),对照内部资产,产可执行产物。全部链接可溯。

## 一、学界业界最新 vs 我们的资产(对照表)

| 外部发现 | 对照内部 | 判读 |
|---|---|---|
| **研究空白**:无单篇覆盖"量化×小判分×鲁棒性"(SLM-as-judge survey 亦称小判分鲁棒性研究不足) | PRECOR B/C 判定表(fp16 1.0/int8 98.28/int4 94.16,291 题) | **我们已站在空白上——可首发** |
| 量化行为变化已有预注册研究(LessWrong 2026-08) | PRECOR 同方法论 | 方法论互证,引用之 |
| 离散判据平局率高(1-5 制 88/100 tie)→学界转向连续 logprob 打分 | PRECOR-C 软维度门(相邻档) | **方法学直接吸收**:软维度改连续分数口径 |
| RIPD rubric 偏好漂移攻击(promptfoo):自然语言 rubric 可被操纵 | 判读安全(判据注入防御空白) | **新安全项**:判据修订序 v2 加漂移注入测试 |
| Claw-SWE-Bench(2606.12344):通用 harness 评测基准 | caliber-bench(测评测本身可信) | 同赛道进入者,定位互补:它们测效率,我们测可信——白皮书引用作"赛道被验证"证据 |
| 行业口径:"SWE-bench 不宜作采购唯一依据" | 我们 Round1 污染 caveat 同款口径 | 行业向我们的方向走,对外文案可引 |
| Replay buffer:混 5-20% 旧样本关闭 60-80% 遗忘差距 | P3 delta 训练(33/200) | **训练配方直接吸收**:delta 批次混 10-15% 锚定集(split_train 抽样) |
| MemRL(2026-02):冻结 LLM+情景记忆非参数自进化 | compass 双层记忆设计(外挂事实+权重技能) | **外部印证同构**;M7b(M5 部署)优先级依据+1 |
| Agent Distillation(NeurIPS 2025):LLM agent 蒸馏进小模型(code-as-memory) | v5 涡轮增压(r84 64%) | 学术同类,方法可借鉴(code-as-memory 进蒸馏配方) |
| Agent-in-the-Loop(Uber EMNLP 2025):生产飞轮四类标注 | TURBO 管道 | 标注类型设计可借鉴(preference/rationale/relevance/missing) |
| TTT test-time training(2026-01) | 域适配判分(具身/agent 域切换) | 新工具候补,P3 域适配实验备选 |

## 二、产物清单(按开业优先级)

1. **[新] PRECOR 判定表→技术短文**(开业后一周内):填研究空白首发,arXiv 短文或官方博客——组织学术信用+元基准引流双收;素材全在档(判定表+matrix+run.log);
2. **[增] 判读安全项**:rubric 漂移注入测试进判据修订序 v2(PRECOR-C 补跑时一并设计);
3. **[改] 软维度门方法**:PRECOR-C v2 采连续 logprob 口径(替代离散相邻档),学界趋势对齐;
4. **[配] P3 训练配方**:delta 批次混 10-15% 锚定回放(防灾难遗忘,学界配方),写进训练复考段 SOP;
5. **[引] 白皮书/BP 引用更新**:Claw-SWE-Bench(赛道验证)+量化预注册研究(方法互证)+行业 SWE-bench 口径(我们 caveat 的行业印证)——随 v1.5 补全窗插引;
6. **[报] zenmind 通道**:自动 digest 机制实证在跑(15 封积压),BYZ 裁决前为唯一活性证据——platform 台账收录(已 ack 建议收录)。

## 三、同步各框

- **v5**:Agent Distillation+MemRL 两方法可入涡轮增压与记忆自进化配方(函附);
- **flywheel**:MLLM 持续学习综述(440 篇)+具身域 continual learning 赛道 2026 三倍增长——具身小模型训练的学界地图(函附);
- **platform**:白皮书引用更新清单(第 5 条)+leaderboard 404 催办已发。

—— compass · 2026-10-07 · RESEARCH-SYNC-V1
