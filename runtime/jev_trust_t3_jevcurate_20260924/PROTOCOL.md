# T3 mini 校准 · jev-curate reasoning-math(预注册 · 2026-09-24)

> 甲方:jev-curate issue #3(AkashPriyadarshii 接单,回执 issuecomment-5798197880)。
> 范围:mini 免费,甲方指定 reasoning-math preset + mock_test.rs 测试行。
> 交付物(甲方判据原文):accuracy / Brier / ECE + 一个阈值修复 + raw artifacts;
> 未经许可不发布。
> 本档开工落死判据(报数纪律:判据只许更严;零 API 调用时写下)。

## 样本(5 行,jev-curate tests/mock_test.rs evaluate_record 全集)

| # | 文本 | mock 手写值(对照用,非 Jev 输出) | mock 测试意图 |
|---|---|---|---|
| R1 | `Let f(x) = x^2. By taking the derivative with respect to x, f'(x) = 2x.` | noul=0.05 score=4.8 conf=0.95 | pass |
| R2 | `P is true because P is valid, therefore P is established.` | noul=0.95 score=4.0 conf=0.90 | reject(noul 腿) |
| R3 | `The answer is obviously 42, trust me on this.` | noul=0.10 score=2.0 conf=0.90 | reject(depth 腿) |
| R4 | `Step 1: Compute matrix determinant. Step 2: Invert matrix.` | noul=0.10 score=4.5 conf=0.30 | reject(conf 腿) |
| R5 | `Let a = 1 and b = 2. Then a + b = 3.` | (response 缺 reasoning_depth) | fail closed |

注:mock 值是 wiremock 手写理想值,为测过滤逻辑设计,**不是校准真值**;R2 mock
score=4.0、R4 mock score=4.5 与数学直觉偏离较大,报告将如实并列。

## 独立真值标注(预注册时刻写死)

| # | circular(1=含循环/同义反复/预设结论) | depth(1-5) | 理由 |
|---|---|---|---|
| R1 | 0 | 4 | 正确一步求导,清晰但无 pedagogical 展开(≠5) |
| R2 | 1 | 1 | 纯同义反复,零推导 |
| R3 | 0 | 1 | 纯断言;无推理链但未把结论当前提使用→非循环 |
| R4 | 0 | 2 | 步骤名罗列,零中间步骤/零执行 |
| R5 | 0 | 2 | 平凡正确,detail 为零;"standard detail"=3 的分界未达 |

敏感点预披露:R5 depth 主标 2;若复算员独立标 3,则 depth-MAE 变 ±0.2,
3.0 线上 R5 判定反转(2→应拒/3→应留)——复算按复算员标注如实双报。

## 调用规格(与 jev-curate 生产同构)

- endpoint `https://api.typesafe.ai/v1/systemone`
- **model=`jev-1.13.0`**(jev-curate client.rs 写死的生产版;不用 jev-latest)
- state=`{"text": <行原文>}`(filter.rs evaluate_record 同构)
- questions=presets.rs reasoning-math 两问原文(instructions 逐字),
  两问一批一次调用;每行独立调用,共 5 次;内容零重试;间隔 ≥0.3s

> **修正记录(2026-09-24,主批零正式调用前)**:格式探针(probe_format.py,
> 不计入指标)实测:①score 类问题 `criteria` 服务端要求**字符串数组**,
> jev-curate presets.rs 的 dict 形式在真 API 必 422(其 mock 全为手写
> wiremock,该格式从未过真 API);②真 API score 为 **0-4 标尺**(响应含
> legend 0-4,score=各档概率期望),甲方 rubric 为 1-5——判据主口径
> 换算写死:depth_1based = score_0based + 1,原始 0-based 值同步落工件;
> ③探针样例 score 答案 confidence=0.0,主批如实记录(若全 0,甲方
> min_confidence=0.5 腿在真 API 上将全量拒收——如实报)。
- 对照批(可选,预注册声明):同规格跑一遍 model=`jev-latest`,单列对照不进主判据
- 全量 session.jsonl 落账 + sign_log 签名 + pubkey 落盘

## 指标口径(写死)

noul 腿(p_i = Jev 输出 noul 概率,y_i = 真值):
- accuracy@0.70:sign(p_i≥0.70)==y_i 的行占比(拒/留判定对真值)
- Brier:mean((p_i−y_i)²)
- ECE:10 等宽桶,ECE=Σ_k |B_k|/n·|acc_k−conf_k|(noul 腿 conf=该 answer 的 confidence)

depth 腿(s_i = Jev 输出 score,d_i = 真值):
- MAE:mean(|s_i−d_i|)
- accuracy@3.0:sign(s_i≥3.0)==sign(d_i≥3) 的行占比
- conf 腿:confidence<0.5 的行逐行列出(甲方 min_confidence=0.5)

mock 对照列:mock 手写值按同口径算一份(对照,不进判据)。

## 阈值修复

非预注册项(分析产物):按实测读数给一条建议(方向:0.70 noul 阈 / 3.0 depth
线 / 0.5 conf 线三选一),报告须给依据行。

## 收工

RESULTS.md(读数+对照+建议)+ raw artifacts(session.jsonl/.sig/pubkey/
t3_results.json/decision 文本内嵌);**待非实现者复算**(新会话只信本档判据
与工件,独立重标+重算);对外发布需甲方许可。
