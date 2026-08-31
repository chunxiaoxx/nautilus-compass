# d13 judge-重判 预注册判据(2026-08-31,重判执行前落盘)

> 本文在重判执行**之前**写入,防事后挑口径。重判动机:d13 双域 RAW 判分被 ARK coding plan
> 限流风暴污染("empty response content" 250 次,16 路并发触发),RAW 是下界口径,不能定案。

## 背景读数

- d12 基线(干净口径):web **0.367** · ent **0.403**
- d13 RAW(污染口径):web **0.2833**(240 题)· ent **0.3081**(211 题)
- 污染分流(per_question.jsonl `eval_function` 字段):
  - 确定性判分(norm_phrase_set_match / mc_choice_match / norm_phrase_set_match_ordered)
    零分 = 模型真实答错,**不可重判**(判分器没挂)
  - LLM judge(llm_abstention_checker / llm_gotchas_checker)零分 = judge 挂掉污染,**可重判**
  - 量定:ent 污染 40 题(32 abstention + 8 gotchas)· web 污染 60 题(53 + 7),合计 100 题

## 重判协议(预注册)

1. **范围**:仅上述 100 题;其余分数原样保留。
2. **judge prompt 与管线**:与 d13 同款(源码 `evaluation/harness.py` 的 checker prompt,
   从保留盘抢救回的源码为准);evaluator 同款 doubao-seed-2-0-pro-260215,ARK coding plan 端点。
3. **并发与退避**:单并发;429/empty response 指数退避(1s→2s→4s→…上限 60s,每题最多 6 试);
   6 试全败则该题保留原 0 分并计入"重判失败"披露。
4. **合并规则**:新分数 = max(原分, 重判分)。重判只升不降(原分下界口径的一致延伸)。
5. **成本**:重判为纯 LLM 调用(100 题 × 1 次 judge),无 GPU。
6. **披露**:重判后 aggregated 同时披露 RAW / 修正后两套口径与重判成功率。

## 定案判据(预注册,沿 d13 开跑前判据)

修正后口径对照 d12:

- 任一域 ≥ d12 同域 **+5pt** → 该域过门(刀3 检索器在该域 PROVEN)
- 双域均 <+5pt → 刀3 全量验证 **路线关闭定案**(d12 检索栈维持现役)
- ent 逼近过门线 0.453 = 修正后上限(web ≤0.538 / ent ≤0.498)情形下的关键观察点

## 诚实边界

- 重判仅修复"judge 挂"污染,不修复 reader 侧任何问题。
- 零分下界逻辑:修正后数字仍可能低于真实水平(judge 单次重判仍有随机性),方向只会更悲观不会更乐观。
- 判据于重判前锁定;若重判失败率 >20%,结果降级为 INCONCLUSIVE 而非定案。
