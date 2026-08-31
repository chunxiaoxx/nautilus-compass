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

## 执行口径更正(2026-08-31 22:30 跑前落盘 · 用户拍板 d14→s250 后)

- **执行环境**:652957(lyg1024/4090PLUS 48G,652509 保留盘恢复,老环境原样)。embedder 已从刀3 merged(`/root/knife3/bge-m3-lmev2`,d13 残留)切回基线 `/root/models/bge-m3` —— d14 锚=d12 栈+刀4 单变量(刀3 已因 d13 定案关闭,不叠加)。cfg 改前备份 `compass_cfg.json.d13-bak`。
- **刀4 patch 已应用**:PATCH_OK 64493→65358B(import 语法门过,备份 harness.py.orig-d4)。smoke 10 题 reader 侧无崩溃(patch 不破坏生成)。
- **judge 口径更正:medium/4096 → low/16384**。原因:d14 smoke 复现 d13 风暴——smoke 判分 attempt 1/2/3 全空 + 外层重试也空(结构性 token 预算故障,重试无效)。沿用污染口径 = d13 事故重演。
- **d12 锚同步重判**:为避免"两把尺子"(d12 的 0.367/0.403 含 medium/4096 系统性压 0 偏置,而 d14 用 low/16384 会口径性虚高),d12 全部 451 题(web 240+ent 211)将用 low/16384 同口径离线重判(d13 retry 工具链复用),判据中所有 d12 锚数值(abstention 得分率/overall 门线)以重判版为准。定案文档同时给污染版/重判版两行,判据结构(上述 5 条)不变。
- **questions/haystack 复用 d13 runtime**(240/211 同题同序,与 d12/d13 可比)。serial 链 web→ent(BGE 竞态禁并行进程),reader 16 并发与 d12 一致。
- 时间线:8/31 22:20 web 启动,预计 9/1 凌晨全程完成;完成后 s250(vLLM qwen1.5b 8023)接续。
