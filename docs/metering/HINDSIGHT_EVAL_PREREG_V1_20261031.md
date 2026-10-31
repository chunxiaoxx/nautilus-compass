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

## 五、资源与技术路线(10/31 侦察后定稿)

- **hindsight 臂无需 GPU**:自托管=Docker(`ghcr.io/vectorize-io/hindsight`·API 8888/UI 9999)+一个 LLM API key(HINDSIGHT_API_LLM_PROVIDER 支持 25+ 家)——本机 Mac(Docker 29.8.2 在)或 cloud 均可跑
- 适配器:其 API 面=`retain(bank_id, content, context, timestamp)` / `recall(bank_id, query)` / `reflect(...)`,Python 客户端 `hindsight-client`——LongMemEval 历史会话逐段 retain → 每题 recall → 召回注入 subject prompt → judge 评分;Python 客户端 `hindsight-client` MIT 协议
- 对照臂(可选 stretch):compass 当前版同协议同跑(绝对读数为主交付,对照臂为加分项);参照读数=compass v0.8 56.6%(2026-05-04·~$3.5 成本)
- subject/judge 模型:与参照跑同款(deepseek-v3.2 经 ARK·judge 分离),保证双臂读数互可解释

## 六、待定项(候 hindsight)

- [ ] version/tag + self-host 推荐配置(其一答即冻结 §三 开跑;tag 未答则用 ghcr latest+commit sha 记录)
- [ ] 代表性数据集(若有→次跑)
- [ ] retain 用 LLM key 选择(其 retain 提取需 LLM——用哪家=其推荐默认,不做我方偏好调优,遵守 §三.1)
