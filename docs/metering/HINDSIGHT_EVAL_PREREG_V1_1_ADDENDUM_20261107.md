# Hindsight 独立评测 · 预注册判据 V1.1 附录(2026-11-07)

> 纪律:V1(`HINDSIGHT_EVAL_PREREG_V1_20261031.md`)判据只许更严;本附录只记录
> **开跑前**(2026-11-07,首个 retain 调用发出之前)锁定的执行参数与两处环境偏离,
> 不放宽任何 V1 条款。hindsight 侧 48h 窗口(我方开工帖 #5584 comment 6704462866,
> 2026-11-07T08:25Z)内无对方回复 → 按 V1 §六默认项执行。

## 一、冻结的执行参数

- **hindsight version**:`ghcr.io/vectorize-io/hindsight:latest`(digest 记录于 freeze 档)
- **hindsight 配置**:其 README Quick Start 默认 Docker 单容器(API 8888),LLM
  provider=minimax(其官方 provider 表内,默认模型 MiniMax-M3),embeddings=local
  BAAI/bge-small-en-v1.5(其出厂默认)。零我方调优(§三.1)
- **bank 协议**:每题一 bank(`lme2-<sha12(sorted haystack_session_ids)>`;实测 500 题
  全互异)。retain 内容=冻结 harness 同款 `session_to_text(max_chars=600)`,
  `document_id=session_id`,`timestamp=haystack_dates`(其原生时间接口)
- **recall**:官方 `hindsight-client` 默认参数(budget=mid, max_tokens=4096),空结果=
  数据照报 0 分(§一)
- **subject/judge**:逐字复用冻结 harness `tests/eval_longmemeval_accuracy.py` 的
  prompt/温度(0.1)/judge 解析/temporal 抽取/单 vote;唯一置换=检索步换 hindsight
  retain→recall。评测器:`tests/eval_hindsight_arm.py`(与 adapter 一并冻结)
- **次级指标**(照报不进判定):per-question-type 分解 · recall document_id 命中率
  (truth_in_top 同口径)· judge 显式失败率 · retain 阶段 wall-clock

## 二、环境偏离(如实记录,预注册时点已尽知)

1. **retain LLM ≠ openai/gpt-4o-mini(其推荐默认)**:金库 OPENAI_API_KEY 已死
   (2026-11-07 实测 401 invalid_api_key),newapi 网关令牌已轮换失效。改用其官方
   provider 表内 minimax/MiniMax-M3(同为出厂默认模型,非我方偏好挑选)。
   base_url 覆写为国内站 `https://api.minimax.chat/v1`(key 属国内站)。
2. **subject/judge ≠ deepseek-v3.2(参照跑同款)**:ARK coding plan 订阅已过期
   (2026-11-07 实测 InvalidSubscription;deepseek-v3.2 亦报 UnsupportedModel,
   按量端点 /api/v3 报模型不存在),参照车道死亡。替代=MiniMax-M3(OpenAI 兼容端点
   实测活,与 retain LLM 同厂)。**后果:与 compass 56.6%(DeepSeek V3.2 subject)
   的对比为跨 subject 模型对比,报告须显式标注,不得声称为同模型 apples-to-apples。**
   (锚点:BENCHMARKS_REPRODUCE.md 记录 MiniMax M2.7 nothink 在 compass 臂为 45.8%,
   同为跨模型参照先例。)

## 三、与 V1 的兼容性

- V1 §一/§二/§三全部条款不变(judge 失败显式 error 禁记 0 · 失败照报 · 单批不跨批
  cherry-pick · 官方推荐配置优先零调优)
- V1 §四"判据冻结后开跑"以 freeze 档(HINDSIGHT_EVAL_FREEZE_20261107.md)落commit 为准
