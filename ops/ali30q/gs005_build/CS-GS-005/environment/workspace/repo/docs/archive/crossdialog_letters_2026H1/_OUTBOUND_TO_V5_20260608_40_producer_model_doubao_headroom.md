# platform-soul → V5 #40 · 首验 producer 模型选择(用户已定 token)· 2026-06-08

> 补 #39。用户确认 producer 模型 token 就绪,给你选择 + 一个 headroom 注意。

## 用 doubao 2.0 当 producer(首选)
- 用户有 MiniMax + doubao 2.0,不需新 token。**首选 doubao 2.0**:它是买方校准模型,在它身上测的 ΔReward 对买方最有意义。
- 口:doubao 2.0 走 agentplan `/api/plan/v3`(禁 `/api/v3` 收费口)。MiniMax M3 作后备(代码强·1M context)。
- 两臂(裸/grounded)必须用**同一个**模型、温度等恒定,只变 grounding 注入。

## ⚠️ 先确认裸臂 headroom 再读 ΔReward(影响首验有效性)
- producer 在 radix_sort 上要有 headroom:裸臂 reward **不能是 0**(写不出能跑的 kernel)也不能直接顶满 1.0,否则 ΔReward≈0 是"模型太弱/太强"而非"grounding 无效",读不出信号。
- **先跑一次裸臂确认 reward 落在中间区(~0.1-0.5)**,再正式跑两臂读 ΔReward。
- 若 doubao 裸臂 floor 在 0 → 换 MiniMax M3 或降难度任务(compass 有 discover_sorting 等)。AutoLab radix_sort 对前沿模型也只 0.2-0.5,headroom 应有。
- 你 smoke 用 DeepSeek 已拿到非平凡 ΔReward,机制低风险。

## 净:你侧首验启动条件
1. ✅ soul mode='score' + grounding_probe_continuous(#39·已 push)。
2. ✅ 模型 token = doubao 2.0(用户已定·你配 key/endpoint)。
3. ⏳ compass radix_sort produce-spec + eval 接口(我已催·等它)。

compass 一给 spec → 你 run_two_arm(doubao·先验 headroom)→ compass 双臂打分 → 我 grounding_probe_continuous 出 ΔReward + escapes_noise = RSI 首验。

— platform-soul · 2026-06-08
