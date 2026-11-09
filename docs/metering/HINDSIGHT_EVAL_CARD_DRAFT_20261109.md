# hindsight 独立评测 · 评测卡(草稿·数字出数即填)

> 状态:eval 500 题跑批中(11/9 09:44 起·ETA ~12:15)。本卡数字全部待填,
> 结论无论好坏照发(预注册 V1 §四)。

## 主读数(判据冻结口径)

- **LongMemEval-S accuracy(hindsight 臂)= __/500 = __%**
- 参照:compass v0.8 = 56.6%(n=500 · 2026-05-04 锁)
- ⚠️ 跨 subject 模型对比(hindsight 臂 subject=kimi-k3 vs 参照 DeepSeek V3.2),显式标注

## hindsight 臂配置(全披露)

- 镜像:ghcr.io/vectorize-io/hindsight:latest · digest `sha256:19d0c08f…` · API 1.2.0
- 部署:Docker 单容器(README Quick Start 默认形态)· embeddings=local bge-small-en-v1.5(出厂默认)
- bank 协议:每题一 bank(500 bank · 25,097 非空去重 session · document_id=session_id · timestamp=ISO 归一)
- retain 提取 LLM(混合·车道枯竭被迫三次切换·勘误1/2 在案):
  - 31 bank MiniMax-M3(11/7-11/8)
  - ~290 bank glm-5.3-flash(11/9,智谱 RPM 档位墙前)
  - ~70 bank kimi k3(11/9,5h 窗口烧穿前)
  - 其余 ~109 bank gpt-5.6-sol(11/9,code80 主+qixuw 备)
- subject = kimi k3(api.chunxiao.wang)· judge = claude-opus-5-5(code80)· judge≠subject(较参照 self-judge 更严)
- prompt/judge/温度/单 vote:逐字复用冻结 harness `tests/eval_longmemeval_accuracy.py`(fa815d3e)
- recall:官方 hindsight-client 1.2.0 默认参数

## 次级指标(照报)

- per-question-type 分解:__(出数填)
- recall document_id 命中率(truth_in_top):__
- judge 显式失败率:__
- 单题成本/wall-clock:__(中转站计费口径)

## 原始产物与复算

- 逐题 jsonl:`/tmp/hs_eval/hindsight_arm_results.jsonl`(拷贝入仓 `paper/results/`)
- run log(全事故链):`/tmp/hs_eval/RUN_LOG.md`
- 复算命令:`python tests/eval_hindsight_arm.py --phase summarize`(冻结 commit 起)

## 预注册与冻结链

V1(10/31)→V1.1(11/7 车道死亡)→V1.2(qwen)→V1.3(中转站终局)+勘误1(kimi)勘误2(gpt)
判读条款全程零变更;全部变更开跑前或跑批中断续行,逐条 commit 留证。
