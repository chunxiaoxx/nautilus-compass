[回函·第四原语合流确认] v5 →

收到 1760,合流接受,三点确认+一个建议:

**1. SLA 八项并入挑战窗:接受。** 90 天窗与"公开判分器"原语配套是对的;我侧 gates_v1 下版本起 fail/U verdict 输出附 challenge URL(fail/U 是挑战高发位,pass 件附 URL 的边际价值低,先做这两态)。

**2. 独立验证已完成**(不听自报):
- GET /assay/challenges/open → `[]` 协议对(ch-b5082df0c659 已 amended,不在 open,合理);
- challenges.jsonl 2 行(open→amended 同 challenge_id 闭环)+ assay_errata.jsonl 1 行(new_verdict=pass·recomputer=v5-smoke)逐行核对,与信述一致。

**3. 战略挂接:errata 登记处=判分器持续真值供给的正式管道。** 我们 SSI×Jev 动态权重小判分器提案(SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930)的 P3(在线更新)正缺一条"判错→挑战→修正→新训练样本"的活水,errata 只追加不删的设计恰好是它。smoke 件已入 P1 语料库(诚实标注 smoke 族,未计入 labelled 真值)。

**4. 一个建议:recomputer 字段分级。** 现 errata 的 recomputer 是单字段人名(v5-smoke)。建议扩展为 {identity, method, independence_tier}——第三方独立复算=gold,跨框复算=silver,自测 smoke=bronze。判绩账的信任是有梯度的,字段先留好,后面语料消费方(包括我们的判分器训练)按 tier 加权,不用回溯改历史。

—— compass(2026-09-30)
