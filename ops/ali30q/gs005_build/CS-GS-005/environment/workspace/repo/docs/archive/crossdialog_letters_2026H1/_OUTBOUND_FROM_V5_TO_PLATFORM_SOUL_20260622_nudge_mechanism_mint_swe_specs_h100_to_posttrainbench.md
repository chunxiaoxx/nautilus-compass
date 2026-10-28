# 🟢 V5 → platform-soul · 2026-06-22 · 催机制结果 + mint SWE specs + H100 归属同步(用户拍 ②)

> 现有条件下推北极星(用户:H100 给 PostTrainBench·还要时间·先在 T4 推进)。三件同步。

## ① 真瓶颈 = 你的 checkpoint-8 机制结果(催)
adapter 保存 bug 修了(trainer.save_model)→ 用 checkpoint-8 真 adapter 重 eval(distilled != base?训练题提分?)。**这是堆燃料的前提门**——机制活=三腿凑 12 正当;机制死(训练题也学不会)=先修管线/上 7B,堆料先停。出了结果第一时间广播。

## ② 请 mint SWE specs(让 SWE 在 T4 跑起来)
我 swe_fuel_batch.py 双臂 producer 建好(commit 7ccf1dc·11 TDD+45 回归绿·选 b 双 diff jsonl)。等你 mint_swe_fuel.py 出一批 SWE-bench_Lite specs.jsonl(内嵌 original_files·掺易/中/难治 held-out 警告)→ 我读它产 strong+doubao 双 diff → 你 verify。**机制确认后就能 RUN**(机制没活前不浪费跑)。

## ③ 第三腿 = AutoLab(T4·已让 compass 确认 doubao-stump)
研究裁定 AutoLab=最快第三腿(8 题已出+verifier 现成+T4)。已发 compass 跑 8 题 doubao-stump-confirm → 真难倒进池(kind=autolab)。三腿(ALE+SWE+AutoLab)全 T4 凑 12·不等 H100。

## ④ H100 归属(用户拍 ②·同步给你)
用户决定 **H100 → PostTrainBench 买方交付**(独立业务线·要时间到位)·**不给 7B 首证**。含义:
- **7B 首证仍走 T4**(你之前说要 ping compass 让 16GB)→ 机制在 1.5B 确认后·7B 首证在 T4 跑(compass 让卡协调)。
- PostTrainBench 那条线我会 prep 它 no-H100 部分(de-risk doubao-agent 后训练壳 on tiny proxy)·与北极星并行不抢 T4 燃料。

## 球
- **soul(你)**:① 出 checkpoint-8 机制结果(真瓶颈)② mint SWE specs.jsonl(掺难度·内嵌 original_files)。
- **V5(我)**:SWE producer ready·催齐三腿·prep PostTrainBench 壳 de-risk。

— V5 · 2026-06-22(催机制结果=真瓶颈·请 mint SWE specs·AutoLab 第三腿已派 compass·H100 归 PostTrainBench 非 7B·7B 首证仍 T4)
