# Hindsight 独立评测 · 预注册判据档 V1

> 线:unipat/验证机构(判读免费) · 对象:vectorize-io/hindsight(其 10/22 明绿灯:"free to evaluate and publish, 只要 eval code 公开源")
> 纪律:报数纪律(开工先落预注册判据档,判据只许更严)·证据分层·结果无论好坏照发
> 状态:**判据冻结候选,候 hindsight 答复两问后定版执行**(答复版本/config 后写入 §三 才开跑)

## 一、基准与协议(冻结候选)

- **主基准:LongMemEval-S**(与 compass v0.8 的 56.6% 同协议同判据——apples-to-apples,双份读数互相可解释)
- harness:`tests/eval_longmemeval_accuracy.py`(本仓 OSS,已公开)·参照档 `BENCHMARKS_REPRODUCE.md`
- 判分:LLM judge 与 subject 分离;judge 调用失败记 **显式 error 并重试**,禁止记 0(该缺陷即我们在 letta#340 指出者,自家协议不得重演)

## 二、指标(主次分层)

- **主读数**:LongMemEval-S accuracy(单口径,全对记 1 否则 0)
- 次披露(照报不进判定):per-question-type 分解·单题成本·wall-clock·judge 显式失败率

## 三、公平性规则(冻结候选,候定版)

1. hindsight 安装=**其官方文档推荐配置优先**,不做针对我方 pipeline 的调优;version/commit 由其指定(已函问,trace compass-20261030-gs005-erratum 无关——实际问题坐标:hindsight#5584 我方回帖 6537044340)
2. 其若提供"代表性数据集"→ 作为**次跑**加入,不替换主基准
3. 失败/零答=0 分**照报**,禁静默跳过;环境故障导致的失败须当场留证并单列
4. 单批跑完,不跨批 cherry-pick

## 四、冻结与发布

- 本档+harness commit sha16 冻结后开跑;判据变更=新版本档,禁原档放宽
- 发布物:报告+全部原始结果文件+逐条 recompute 命令——hindsight#5584 线程回贴链接
- 时点:hindsight 答复两问后 7 天内出报告(GPU 资源:外部 T4/A100 或本机,依其 self-host 资源需求定)

## 五、待定项(候 hindsight)

- [ ] version/commit + self-host 推荐配置
- [ ] 代表性数据集(若有)
- [ ] 资源需求确认(决定 GPU 租用规格·参照 GPU 实例复用纪律)
