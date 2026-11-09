# hindsight 独立评测 · 评测卡(终版 2026-11-09)

> 判据预注册 V1(10/31)+V1.1/V1.2/V1.3 附录与勘误 1/2 · 结果无论好坏照发(V1 §四)
> 主读数两轮:pass1=31.0%(judge 瞬时 400×138 照报)→ 按预注册重试条款单轮补判 → **终版 40.8%**

## 主读数

| | LongMemEval-S accuracy(n=500) |
|---|---|
| **hindsight(本次独立评测)** | **204/500 = 40.8%** |
| compass v0.8 参照(2026-05-04 锁) | 283/500 = 56.6% |

⚠️ **跨 subject 模型对比**:hindsight 臂 subject=kimi-k3/judge=opus-5-5;参照=DeepSeek V3.2
self-judge。两臂 prompt/judge 协议/温度/单 vote 逐字同款(冻结 harness `fa815d3e`),
仅 LLM 车道不同(车道枯竭史见 run log)。对比结论须带此星号。

## per-question-type

| type | n | acc | 检索命中* |
|---|---|---|---|
| single-session-preference | 30 | 50.0% | 100% |
| temporal-reasoning | 133 | 52.6% | 99.2% |
| multi-session | 133 | 42.1% | 100% |
| knowledge-update | 78 | 42.3% | 100% |
| single-session-assistant | 56 | 32.1% | 98.2% |
| single-session-user | 70 | **17.1%** | 100% |

\* truth_in_top:recall 返回的记忆中含答案所在会话(document_id 回溯)——**498/500=99.6%**,
hindsight 的检索几乎总是把对的会话内容带回来;失分主因在 subject 组装作答层
(尤其"用户自己说过什么"类,subject 常答"未提及")。

## judge 显式失败率

- pass1:138/500(27.6%,code80 瞬时 400 全同型)→ 单轮补判(预注册 §一重试条款)
- 终版残余:32/500(6.4%),按显式 error 计 0 分照报,未做第二轮补判(防选择性重跑)

## hindsight 臂配置(全披露)

- 镜像 `ghcr.io/vectorize-io/hindsight:latest` · digest `sha256:19d0c08f…` · API 1.2.0 ·
  Docker 单容器出厂默认(embeddings=local bge-small-en-v1.5 · 服务端槽位默认 10)
- bank:每题一 bank,500 bank / 25,097 非空去重 session;retain 内容=harness 同款
  session_to_text(600);document_id=session_id;timestamp=ISO 归一(haystack 日期)
- retain 提取 LLM 混合(车道枯竭四次切换,勘误链在案):31 MiniMax-M3 · ~290 glm-5.3-flash ·
  ~70 kimi-k3 · ~109 gpt-5.6-sol(code80 主+qixuw 备)
- subject=kimi k3 · judge=claude-opus-5-5(judge≠subject,较参照 self-judge 更严)
- recall:官方 hindsight-client 1.2.0 默认参数(budget=mid);空 recall=0 分照报(实测未出现)

## 原始产物与复算

- 终版逐题:`paper/results/hindsight_arm_results_final_20261109.jsonl`
- pass1 原始件(138 error 未补判):`..._pass1_20261109.jsonl`
- 全事故链 run log:`docs/metering/HINDSIGHT_EVAL_RUN_LOG_20261109.md`
- 复算:`python tests/eval_hindsight_arm.py --phase summarize`(冻结 commit 89768c2f 起)

## 结论(如实)

1. hindsight 检索层极强(99.6% 命中),端到端读数受 subject 组装能力与判卷残余错误压制
2. 与 compass 56.6% 的差距(-15.8pp)为**跨模型对比**,不可归因于系统本身
3. 本次评测自身教训:提取负载(25K 次 LLM 调用)远超订阅制车道承载力,四车道枯竭切换
   全程留证——对外评测的 infra 预算应在开工前按量核定
