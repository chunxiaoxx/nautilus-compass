# d14 预注册判据 · 刀4(abstention gate)· 2026-08-30

> 立此为锚于 d14 跑前。对照锚 = d12(刀1+刀2,embedder 基线版)与 d13(刀1+刀2+刀3 merged embedder)。
> d14 = 刀1+刀2+刀3+刀4 叠加(若 d13 已换 merged embedder,则 d14 仅新增刀4 一个变量)。

## 根因(d12 web dynamic 3 道掉分 1.0→0.0 逐题对齐)

- `609acb91` / `96497069`:快照含直接证据,reader 却走 "lack access to the live environment" 拒答模板 = 刀1 路线3 过度泛化。
- `2ee130d2`:答案 False 正确但 boxed 内附矛盾解释,mc_choice_match 严格匹配失败 = 格式污染。

## 判据(跑前钉死,事后不改)

1. **误拒答根因型**:web 上"answer 含 lack-access 模板但 gold 可从快照验证"的题 ≤ 1 道(d12 = 2 道,均为已证根因题)。ent 同口径 ≤ 2 道(d12 抽样未见,留余量)。
2. **刀1 主收益不丢**:abstention 组得分率 web ≥ 35%(d12 = 45.8%)、ent ≥ 70%(d12 = 83.9%)。
3. **格式污染型清零**:mc_choice/短语匹配题中"gold 语义出现在 answer 内但判 0"的题 = 0(逐题 grep 复核,允许表述差异)。
4. **overall 不回退**:web non-abst overall ≥ 0.327、ent ≥ 0.245(d12 锚);若 d13(刀3)已涨,d14 ≥ d13。
5. **dynamic 分项**:web ≥ 0.137(d12)且无新增"快照有证据却拒答"型 0 分题。

## 跑法与纪律

- 执行时点:**d13 双域跑完后**才执行 patch(d13 ent 接续是新进程会重读 harness.py,提前执行污染 d13 双域一致性)。
- patch:`/root/knife4/lmev2_harness_prompt_patch_d4.py`(已上传,已本地 dry-run 三断言:regex 恰 1 处、ast 语法门、surgical diff 其余字节不变)。
- smoke:patch 后先 10 题混合冒烟(含 dynamic 型 ≥3 道)确认无崩溃再全量。
- 输出:`/root/lmev2_runs_d14/`,judge/subject 与 d13 同款(doubao plan 端点)。
- 判分互核:d14 与 d12/d13 同 judge 同口径,掉分题逐题对齐 evidence 后才允许归因。
