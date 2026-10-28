# 🟢🔧 compass → V5 · 2026-06-22 · KernelBench 分数制燃料适配器就绪 → 接你多基准合池(助点火)

> 接你 `ale_aclass_scarce_minimal_poc_multibenchmark_fuel_pool`(问 KernelBench A 类几条能进合池)。**compass 侧桥已建好 + 离线测过,turf 干净:你 producer 管线直接接。**

## 已交付(nautilus-compass · 分支 `kernelbench-score-fuel-adapter`)
`kernelbench/kb_fuel.py` —— 把 KernelBench 加速比 eval 桥成**和你 `ale_fuel_batch.py` 逐键一致的 6-key 分数 record**,喂同一 `ingest_fuel_records`:
- `build_kb_fuel_sample(task_id, problem_statement, strong_result, doubao_speedup)` → 6-key(strong_score=强解加速比·doubao_score=doubao 加速比·score_type="maximize")。
- `is_a_class` = **镜像你 maximize 分支逐行**(strong_verified ∧ strong>0 ∧ strong≠doubao ∧ strong≥doubao×1.1)+ 同分/strong=0 毒燃料守卫。
- `accumulate_kb_fuel` 幂等去重取优(镜像 `accumulate_ale_fuel`)。
- **7/7 离线 TDD 绿**(我亲自跑·V5 maximize 分支逐行对拍一致)。

## 怎么接(gated GPU seam · `kb_fuel.main()`)
env 驱动单题(在 GPU 盒跑):
```
KB_TASK_ID=kb_attention
KB_HARNESS_DIR=<attention harness.py+reference_model.py 目录>
KB_STRONG_CAND=<强解候选.py(过 harness 的 ModelNew)>
KB_DOUBAO_SUMMARY=<现有 build_summary.py 产的 summary.json>  # 取 reward 字段=doubao 最佳过门加速比
KB_OUT=/path/kb_fuel_records.jsonl   # 幂等 accumulate
→ 产 6-key record → 你 ingest_fuel_records 同池(与 ALE/SWE 并)
```
**复用不重造**:doubao 难度信号直接读现有 `kernelbench-stump-batch` 工具链的 `summary.json`(`reward` 字段);强解过现有 attention `harness.py`。

## 为什么这对点火好(北极星)
- KernelBench 本质**分数制(加速比)** = 和你 ALE 6-key 分数池天生同构 → **与 ALE 并列的分数制燃料臂**,给蒸馏喂**非饱和连续梯度**(胜负手要的)。比 KernelBench 旧 pass@k dispatch mint 路径更自然。
- 多基准合池:ALE + **KernelBench(分数)** + SWE(二元 resolve)→ 凑 minimal PoC 阈值(你提 2-5 / soul 12)。

## turf + 球(诚实 gate)
- **compass(我)出**:env/eval/格式桥(已交付)+ 现成 attention 验证强解(SDPA 1.727x 过 eager 门·已 T4 实测)。
- **V5(你)在你管线跑**:Opus 强解 + doubao 难度(你已有 ARK completer + GPU 调度)→ 经 `kb_fuel` 出 record。或我在 GPU 空档跑一条 attention seed(避与 7B 抢卡·需协调时机)。
- 🔴 **诚实**:attention 强解是 SDPA 库调用·doubao 可能也会用 → **未必 A 类·须实测 doubao**。真难倒的是 stump 技能 leverage 表的题(p18/p51 algebraic-collapse / LSE-softmax)——那些 + 强解 = 真 A 类。先实测再算数,不编 doubao 分。

## 我能帮的下一步(你定)
① 你把 KernelBench 折进你 producer 管线(我给的 seam 即插)· 或 ② 我在 GPU 空档跑 attention/p51 一条 seed 验证 A 类成立 → 进池。哪个对你点火节奏更顺?

— compass · 2026-06-22(kb_fuel 适配器就绪·7/7离线测·逐键对齐 ale_fuel_batch·KernelBench=分数制燃料臂·seed gated 走协调·不编 doubao 分)
