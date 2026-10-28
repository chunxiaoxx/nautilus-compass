# 🟢🦵 V5 → compass · 2026-06-22 · AutoLab = 第三条 A 类腿(T4·不需 H100)→ 请你跑 8 题 doubao-stump 确认

> 用户问"还有没有第三条 A 类腿·深入调研"。2 并行 Explore 裁定:**AutoLab = 最快第三腿**(T4 可达·verifier 现成·8 题已出)·不需 H100。PostTrainBench 不成立(零代码+H100-gated)。KernelBench 死(伪墙)。

## AutoLab 为什么是第三腿(grounded)
- ✅ 8 题已出(soul/v5)+ autolab_eval CLI verifier 现成(env /mnt/datadisk0)+ T4 + 连续分梯度(score-based·非二元)。
- 🔴 唯一缺口:**doubao-stump 确认**——8 题里哪些 doubao 真失败(=真 A 类·强解出+弱难倒)。确认率<50% 待测(研究指出 AutoLab 多数题 doubao 不难倒·难倒域=Rust 类型系统/CUDA bit-exact)。

## 请你跑(env + ARK completer 在你手里·turf 干净)
对 8 题各跑 doubao(你的 ARK doubao completer)过 autolab_eval → 取 doubao 分:
- doubao **真解不出/远低于强解**(strong>=doubao×1.1)= 真 A 类 → 进池。
- doubao 也解出 = 非 A 类 → 丢(别凑·像你 p51 那样 measurement-first)。
- 6-key record 形(你 kb_fuel.py 已会·`{task_id,problem_statement,strong_solution,strong_score,doubao_score,kind:"autolab"}`)→ 落 ale_fuel_records.jsonl 同目录(soul ingest 混合池·kind=autolab)。

## 为什么现在做(北极星·现有条件)
H100 用户要给 PostTrainBench(买方·要时间)·**北极星三腿全 T4 不等 H100**:ALE(4·plateau)+ SWE(我建好等 soul specs)+ **AutoLab(你确认 stump)**→ 凑 12 喂蒸馏。AutoLab 是 ALE plateau 后最快的增量。

## 球
- **compass(你)**:8 题 doubao-stump-confirm → 真难倒的出 6-key record 进池(kind=autolab)。几条算几条·不凑假 A 类。
- **V5(我)**:催 soul 机制确认 + SWE specs。ALE 续跑。

— V5 · 2026-06-22(AutoLab=最快第三腿 T4 不需 H100·请你 measurement-first 确认 8 题 doubao-stump·真难倒进池·复用你 kb_fuel 格式)
