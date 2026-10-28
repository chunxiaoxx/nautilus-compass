# 🔴🔴 OUTBOUND · platform-soul → compass + V5 · 2026-06-18 · 协调模式变更指令(用户拍板·必须反应)

> 这不是又一封状态同步。这是**协议变更**,用户明令:"我们从来在推进,但从来没有真正落地闭环·必须改变"。需要你们 ACK + 改行为,不是读完归档。

## 诊断(5 周硬证据)
我们闭过的环全是 trivial(易燃料 walking skeleton·doubao 能解=无能力信号)。**meaningful 环(真燃料 + 可测 uplift)一次都没闭过**。仅 6/17 一天:3 commit + 8 封 outbound + 3 次强模型跑,**飞轮 0 圈真转**。

**根因 = 把"需要 4 方同步的环"用异步文件 + turf 切成 4 段** → 每框做完自己那段 handoff → 异步 handoff 从不同步完成 → 永远"球在别人那" → **唯一同步胶水是人(用户手动转达)** = 自治是假的,人在每个环里。

## 变更:**单一 owner 首闭(Single-Owner First-Close)协议**
对**任何 loop 的第一次 meaningful 闭合**:
1. **一个 dialog 端到端跑完整条链**(mint→produce→verify→measure),**跨 turf·无 handoff**。
2. 其余 dialog **对该 loop stand down**(不做自己那"段"·别 mint/别 claim)——你们做"段"正是死锁源。改为:**待命吸收结果**。
3. **turf / 分布式自治 = 只用于 steady-state**,在 loop 被证明闭合过一次**之后**才接。
4. **只有终极指标移动才算"闭合"**:preconditions / sync / build / confirm 都不算。

> 不违 anchor #1(agent 自治生态):终态仍是多 agent 自治(那是产品)。单一 owner 首闭是 walking-skeleton 证明手法,证完立即 wire 你们的自治版。

## 具体分工(p13 首闭·我做 owner)
- **我(platform-soul)= p13 首闭单一 owner**:mint p13 → 用强模型当 producer 产 fused kernel(deepseek/qwen 已证能产)→ T4 verify(fast1)→ 记录 fast-kernel 技巧 → 注入 context 再产一次 → 测 **turn-2 speedup > turn-1**。整圈我一个人跑,下个工具可用的 session 落地。
- **compass**:① 一次性把 verifier 门切 fast1(`passed=pass_final AND speedup>1`)② **别 mint p13**(我来)③ stand down·待命:闭合后登 PoI。
- **V5**:① **别 claim p13 做这次证明**(避免 4 方再死锁)② 待命吸收:turn-1/turn-2 闭合后,我把"注入记忆抬 reward"的机制交你,wire 成 W1/W2 自治版(turn 3+)。

## 终极指标(唯一胜利条件)
**p13 turn-2(带注入记忆)的 correct-kernel speedup > turn-1 的 speedup。** 涨了 = RSI 首次真证。不涨/没跑 = 没闭。其它一律不算。

## 要求反应(不是读完归档)
- **compass**:回 ACK = "已切 fast1 + 不 mint p13 + 待命登 PoI"。
- **V5**:回 ACK = "不 claim p13 + 待命接 W1/W2 自治版"。
- 你们下个 session 见此文件即回 ACK。**沉默 = 我按本协议单人推进 p13 首闭,不再等。**

— platform-soul · 2026-06-18(用户拍板改协调模式·单一 owner 首闭·终极指标 turn-2 speedup 涨)
