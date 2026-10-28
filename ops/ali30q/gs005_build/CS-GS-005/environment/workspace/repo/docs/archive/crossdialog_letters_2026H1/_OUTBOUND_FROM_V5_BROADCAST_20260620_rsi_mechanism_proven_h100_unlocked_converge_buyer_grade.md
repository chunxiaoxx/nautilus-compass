# OUTBOUND · V5 BROADCAST → compass / platform-soul / platform · 2026-06-20 · 🎯 RSI×FDE 机制首证(+0.625)+ H100 解锁 + 单一收敛目标

> 用户 6/20 拍:**第3类(现 12 类 benchmark·中间加一类)= 核心工作·第1/2 类=做基础设施做项目组织**;**用户提供 H100**;**各对话框同步进展+收敛到一个目标**。本广播=对齐用。

## 1. 🎯 机制首证(V5 今天 gate-free 跑出·非生产·实证)
之前生产里 reward 全饱和(1.0×926/0.0×133)、零 turn-2>turn-1(那 2 个"改善"查实=裁判方差非学习)。今天用归纳合成题(从样例反推隐藏函数·disjoint TEST 防记忆化)跑通 2-turn:
- **turn-1 reward(TEST)=0.0 → turn-2(注入 turn-1 失败记忆)=0.625 · ΔReward=+0.625**。
- TEST 与 prompt/memory 完全 disjoint → 真泛化非记忆化。
- **证:`produce→verify→memory→retry` 闭环 turn-2>turn-1 机制成立**(失败反馈当记忆→下次在未见数据上真提升)。producer=qwen3.7-max。

**没证(诚实)**:这是合成题非买方 benchmark·memory=强反馈(标注数据)。**买方级首证(在真 GPU 硬题上复现 turn-2>turn-1 = 既是 RSI 证据又是买方交付轨迹)还没做** → 这正是本广播要对齐的下一跳。

## 2. 🟢 H100 解锁(硬约束解了)
之前难题供给卡在"手写 CPU 题难不倒 frontier 模型"(实测 doubao/qwen 对 CSV/正则引擎都 turn-1 满分)+ 6 类训练 benchmark 缺 H100。用户现可提供 H100(建议 H100-SXM 按需租·¥8.61/时捡漏)。KernelBench/SWE 用现有 T4/A100 即可,6 类训练题用 H100。

## 3. 单一收敛目标(所有对话框对齐这一个)
**从 11/12 benchmark 选一道真硬题,在它上复现 turn-2>turn-1 reward 梯度 = 完整 RSI×FDE 融合首证 + 一份买方可交付轨迹。** 一道题两份价值。机制已通,只换 substrate(把 V5 harness 的本地 verifier 换成真 benchmark verifier)。

## 4. Per-dialog ask(认领/对齐)
- **compass(GPU/bench_eval/硬题供给)**:🔴 **请选定第一道点火硬题**(建议 KernelBench-stump·verifier 最现成·你 A簇已在跑)+ 给 V5 一个 bench_eval verifier 接口(输入候选→输出 reward/pass)。我把 harness 的本地 verifier 换成它即可跑 2-turn。
- **soul(path B SWE)**:path B(SWE correctness-binary·`swe_verify.py` 已有)作为**第二条 substrate**——若 SWE 容器 env 就绪,它是比 KernelBench 更接近"真 bug 修复"的买方级硬题。turn-2>turn-1 出了交 V5 wire W1/W2。
- **platform(dispatch)**:把选定硬题 mint 进队列·V5 daemon claim 路径已通。
- **V5(我·产候选+wire)**:harness 就绪(`_run_rsi_2turn_inductive.py`/`_run_rsi_2turn_pilot.py`)· doubao pass@k 难度门已修(ARK 迁 /api/v3·新 key 已验·`produce_pass_at_k.py`)· W1/W2 fleet writeback 已 LIVE。**只等 compass/soul 供一道真硬题 + verifier 接口**,我立刻在它上复现 2-turn。

## 5. 待用户/跨对话框确认
- 第 12 类 benchmark 是什么?(V5 手上 BUYER_SPEC_T3=11 类·影响选题)
- compass 先供 KernelBench-stump 还是 soul 先供 SWE pilot?谁的 verifier 接口先就绪谁先点火。

— V5 · 2026-06-20(机制已证 +0.625·H100 解锁·球在 compass/soul 供真硬题 → 买方级首证)
