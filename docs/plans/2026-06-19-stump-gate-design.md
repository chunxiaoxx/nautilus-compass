# 设计 · 经验题 doubao stump-gate 产品化(measurement-first)· 2026-06-19

> compass · 飞轮 A(买方难倒题)子件。brainstorming 产出。**本 session 已 ~9h(R3),只到设计;代码+8题良率实测 = 下一 focal session 执行。**

## 背景 / 为什么
用户问题:**如何持续产出难倒 doubao 的真实经验教训题目?** 6/19 实测两道已建经验题(doubao-seed-2.0-pro·N=5):
- d1(version-key-join·**gotcha 型**):pass@5 = **1.00** → 完全难不倒(清晰 spec 把"该考虑版本维度"说破,强模型照做即过)。
- c2(CJK 编码 round-trip·**IO/correctness 型**):pass@5 = **0.60** → 压线难倒(2/5 候选 byte-exact round-trip 全损)。

**判别器假设(N=2·未证)**:难度住"一句 spec 能说清的事"(gotcha→难不倒)vs"模型须在多用例都执行对的 fiddly 正确性"(IO/编码/数值/并发→难倒)。同 KernelBench(写又快又对 kernel 本质难)。

## 🔴 本设计的纠错核心(避免 N=2 过早归纳)
我一度据 N=2 下"良率薄/门按需轻量"——违反取证纪律。**纠正:gate 首先是替代 N=2 的测量仪器。** 先用它测现有 8 道经验题(c2/c2b/c2c/c2d/c2e/c3/d1/d2)的真实 pass@k 良率 → 良率数说话再定:值不值得自动化、门是系统化 step 还是按需、该挖哪类经历。

## Scope(用户拍板)
- ✅ 只做 stump-gate 分拣步 + 自动路由 + 选题启发式(文档)。**不做 daemon 编排**(良率未明前不自动化)。
- ✅ 公平 prompt = 每题显式 `stump_prompt.txt`(solver 视角·不含经验教训/buggy 注释·保留真实约束)。

## 组件
1. **`compass_bench/stump_gate.py`**(泛化今天的 `stump_probe_doubao.py`原型·去掉硬编码 TASKS):
   - 入:`<题dir>`(含 `stump_prompt.txt` + `bench_eval.py`)、`--n`(默认 10)、`--model`(默认 doubao-seed-2.0-pro)。
   - 流:读 stump_prompt → ARK completer 采 N 候选(复用 `nautilus-v5/fde_capsule/_run_bvh_2arm.py: make_ark_completer`)→ 抽代码 → 各跑 `bench_eval.py`(subprocess `encoding=utf-8,errors=replace`·PYTHONUTF8=1·**今天踩过 GBK 崩**)→ pass@k。
   - 出:`<题dir>/_stump_gate.json` = {n, n_pass, pass_at_k, band, route}。
2. **置信带 + 路由**(解 c2=0.6 噪声/迁移风险):
   - `pass@k ≤ 0.2` → **decisive_stump** → route=`buyer_third_class`(可靠燃料·转现有买方第三类交付流)。
   - `0.2 < pass@k ≤ 0.6` → **marginal_stump** → route=`buyer_third_class_provisional`(标"待买方复测·N 加大或加强框法")。
   - `pass@k > 0.6` → **not_stump** → route=`experience_table`(写 tblvR6BCSBH4IG59·无 stump 经验题主轨)。
3. **gate = 证据 + 路由建议,不自动写买方表**。难倒题转现有买方第三类交付流(Opus 4.8 盲解 + 生产轨迹 + 过 AI 检测叙述·见 buyer handoff)。gate 只产 pass@k 这一个输入。

## 数据流
`stump_prompt.txt` →[N×doubao]→ N candidates →[N×bench_eval]→ pass@k →[band]→ `_stump_gate.json` →(人看路由)→ 写对应表。

## 错误处理
- doubao 调用:completer 已有退避重试。<N 成功(API 挂)→ 报 partial + flag,不按 N 算良率。
- candidate 崩/不出码 → 计 fail(等同 buggy·正确)。
- bench_eval 输出含 CJK → 必 `encoding=utf-8`(非 text=True)。
- prompt 公平性:`stump_prompt.txt` 评审规则写进 skill——只说实现什么、不提 bug/修法、保留真实约束;否则判定无效。

## 测试(TDD)
- RED 单测(mock completer·喂固定"3 过 2 挂"输出)→ 验 pass@k=0.6 / band=marginal / route 正确。
- 集成:c2(应 marginal/decisive)、d1(应 not_stump)复现今天结果 = 回归锚。
- 良率实测(首个真用途):8 题各 N=10 → 汇总真实良率表。

## 选题启发式(写进 skill step 1·当文档假设·N=2 不编码成 prescreen)
优先挖 IO/编码/数值稳定/并发-一致性正确性经历(c2 型·stump-prone);少投 gotcha 型(d1 型·spec 一说破就不难)。等 8 题良率验过判别器再考虑静态预筛。

## 诚实边界(写进 skill)
- 经验题难倒**良率可能薄**(8 题实测前是开放问题);**主轨仍是无 stump 的可复现经验题表**(高良率买方产品),难倒是 bonus。
- gate 是**内部筛子**(我的 temp0.7/ARK/bench_eval),非买方终判;边际 stump 未必迁移买方 eval。

## 执行计划(下一 focal session·非本 session)
1. 写 `stump_gate.py`(泛化原型)+ RED/GREEN 单测。
2. 为 c2b/c2c/c2d/c2e/c3/d2 各写 `stump_prompt.txt`(读 task_spec·剥泄题段)。
3. 跑 8 题 N=10 → 真实良率表。
4. 良率定后续:写 skill step 4.5 + 启发式 + 诚实标注;判定飞轮 A 自动化是否值得。

## 关联
memory `session_20260618_pathB_swe_substrate_probe_green_pilot_shortlist`(含 6/19 飞轮A 段)· skill `compass-experience-benchmark` · 原型 `fde_t3_scratch/compass_bench/stump_probe_doubao.py` · FDE_BUSINESS_CHARTER §1.3(第三类 pass@5≤0.6 on doubao)。
