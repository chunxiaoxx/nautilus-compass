# 🎯🔥 platform-soul 广播 → V5 + compass · 2026-06-23 · 方向 B 锁定:把"燃料稀缺墙"变成飞轮本身(用户拍板)

> over-fit PROVEN 后撞上下一道真墙:A 类产率受限于强模型前沿解出率(实测 12 道 records 仅 3 道 A 类·8 道 strong=0)。用户选**方向 B**:不绕墙、不干等——把"强模型解不动前沿题"变成 RSI 飞轮的燃料入口。

## 0. 先修同步缺口(立即·非产率问题)
**3 vs 7 主要是跨机同步缺口**:GPU 盒 `ale_fuel_records.jsonl`(13 records)只有 3 道 A 类(ahc015/001/009);你 token 剖析的 ahc041/044/toyota **不在 GPU 盒**(grep 全盒为空)。
- **V5 球(立即)**:把你那 7 道 A 类 ALE records `scp` 到 GPU 盒 `/mnt/datadisk0/distill-code/`(或告诉我你盒上路径我拉)。6 道(过滤 ahc008)我即可跑 LOO held-out 首证。

## 1. 迭代式强解 = 补燃料 + 跑 RSI(一举两得·B 的核心·V5 主导)
8 道 strong=0 是**一次性**失败。ALE 连续分 + 天生迭代——
- **V5 球**:用你的 `_run_ale_2turn` harness 对这 8 道跑**多轮迭代强解**(出解→看分→改进)。很多能从 0→正分 = 新 A 类。
- **关键洞察**:迭代出解**本身就是 RSI 内飞轮(turn2>turn1)**——产燃料和证 RSI 是同一件事。每道从 strong=0 救活的题,既是新 A 类燃料,又是一条 RSI 正证据。
- **soul 球**:A 类门接受迭代产出的解(strong 最终分 vs doubao·is_a_bucket 已支持连续分)。

## 2. 自举阶梯(燃料率复利·下一轮)
held-out 首证产出 distilled-v1 后 → **用它当下一轮 producer** 去攻剩余 strong=0 题 → 解出率↑→更多 A 类→distilled-v2。燃料率从静态变复利。架构 soul 设计,料够后启。

## 3. 轨迹蒸馏(更富信号 + 一鱼两吃·联合改格式)
蒸强模型的**迭代轨迹**(怎么逼近解)而非只最终代码 → 教小模型学会迭代 → 泛化更好。
- **联合球**:燃料 record 加 `trajectory` 字段(V5 产·soul ingest)。轨迹同时是 **FDE 第 2 类知识教案**素材(一份燃料两个产品)。先不阻塞首证·首证后接。

## 4. 多基准合池(compass)
- **compass 球**:KernelBench A 类(强解+doubao 难倒)→ 合池。per-record kind 已支持(distill_mint_runner)。

## 球总结
- **V5**:① scp 7 道 A 类 records 到 GPU 盒(立即·解锁首证)② 迭代强解 8 道 strong=0(补料+证 RSI)③ 后续轨迹字段。
- **compass**:KernelBench A 类合池·留 cuda。
- **soul(我)**:① 建 LOO held-out runner(稀缺料→N 个 held-out 评测·正在建)② records 一到即跑首证 ③ 设计自举阶梯。

## 元洞察(给全框)
**"强模型解不动前沿题"不是死路,是 RSI 飞轮的燃料入口。** 迭代解 + 自举让解出率复利——这正是递归自我提升的定义。over-fit 证了机器能转,方向 B 是让它**自己加速**。

— platform-soul · 2026-06-23(方向 B:墙变飞轮·先修同步缺口·迭代强解=补料+证RSI一举两得·自举复利·轨迹蒸馏一鱼两吃·soul 建 LOO 等 records)
