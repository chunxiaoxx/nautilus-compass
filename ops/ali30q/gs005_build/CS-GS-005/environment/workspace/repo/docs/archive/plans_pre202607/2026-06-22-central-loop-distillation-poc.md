# 中心环 Forcing Function:A 类燃料→蒸馏 PoC 实现计划

> **For Claude:** REQUIRED SUB-SKILL: 用 executing-plans 逐任务实现。**北极星唯一中心环·出结果前其它冻结**(见 `docs/NORTH_STAR_20260622.md` + 宪章 §0-GOAL)。

**Goal:** 证或杀"蒸馏破能力墙"假设——用甲方 FrontierSWE 基准产 A 类燃料(强模型解+doubao 败+验证器确认),QLoRA 蒸进 Qwen2.5-Coder-7B,held-out 对比 doubao base,赢=飞轮成立放大,平/输=诚实杀假设回护城河副产品。

**Architecture:** 复用现成 minting pass(`fde_double_gate_poll`/`fde_triage`/`fde_strong_gate` 已做"强解+弱败→A/B/C 分拣")+ SWE path B harness(`swe_verify`/`swe_runner`)。新做的只有三块:① 把 double-gate 指向基准实例规模化 + 把 A 类 trace 攒成蒸馏数据集 ② QLoRA 训练脚本 ③ held-out eval。一鱼两吃:A 类 trace = 买方交付物 + 蒸馏燃料。

> 🎯🎯 **首选 workhorse = ALE-Bench(2026-06-22 用户指出·非 FrontierSWE)**:连续打分优化题(无饱和·原生迭代 RSI·infra 轻)。**两处关键差异 vs 二元 SWE**:(a)**A 类判定改连续**——`is_a_bucket` 用"强模型分 ≫ doubao 分"(分数优势阈值)替"二元 pass + doubao fail";(b)**Phase 4 eval 改分数 delta**——蒸馏 7B 平均分 vs base 7B vs doubao(连续·不饱和·比 pass@k 干净)。下面 SWE 任务保留为**次选轨/对照**(二元·已证 path B);**先做 ALE 轨**(需 compass/平台接 ALE-Bench framework+AtCoder 实例+连续 scorer)。FrontierSWE 用同骨架换二元判定即可。

**Tech Stack:** Python · 强模型=qwen3.7-max(百炼 `BAILIAN_API_KEY`)/ Claude/R1(ARK)· 弱模型标尺=doubao-seed-2.0-pro(ARK `ARK_API_KEY`)· SWE 验证=swebench harness on GPU `43.166.8.20`(`/mnt/datadisk0` docker)· 训练=QLoRA/PEFT + Qwen2.5-Coder-7B on A 簇 T4 · 数据=SWE-bench(Lite/Verified)实例。

**🔴 执行 gating:** cloud `ssh -p 24860`(fail2ban·需重加白名单)+ GPU `43.166.8.20`(经跳板)。Phase 1 的纯逻辑(triage/数据集装配)本地可 TDD;Phase 2-4 的强模型 API/GPU verify/训练/eval 需访问恢复。

---

## Phase 0(gating · 非代码):访问 + 燃料源确认

**Step 0.1** 恢复 cloud/GPU 访问(用户重加 fail2ban 白名单或换隧道)。验证:`ssh -p 24860 cloud 'echo ok'` 返 ok。
**Step 0.2** grounding 燃料源真实库存(cloud):`_compass_t3_out/` 现有 FrontierSWE/SWE-bench 复现数据 + SWE path B N=3 trace + AutoLab 8 条。确认强模型已解+验证器确认的 trace 当前实数(= A 类起点)。
**Step 0.3** 确认 SWE-bench 实例集(Lite 300 / Verified 500)+ GPU box swebench 镜像可用范围(Lite 已通·Verified env 待 compass 建)。

---

## Phase 1:A 类燃料 minting pass(规模化 + 攒数据集)· 本地可 TDD 的核心

> 复用 `services/fde_strong_gate.py`(强模型先解)+ `services/fde_triage.py`(三桶分拣)+ `services/swe_verify.py`(swebench 判定)。新建 = 把它们串成"FrontierSWE 实例 → A 类 trace 数据集"的装配器。

### Task 1:A 类 trace schema + 装配纯函数

**Files:**
- Create: `phase3/backend/services/distill_fuel.py`
- Test: `phase3/backend/tests/test_distill_fuel.py`

**Step 1:写失败测试**(trace 装配:强解 patch + 实例 spec + 验证结果 → 蒸馏样本)

```python
from services.distill_fuel import build_distill_sample, is_a_bucket

def test_a_bucket_requires_strong_pass_and_weak_fail_and_verified():
    # A 类 = 强模型解 verified-correct + doubao 败
    rec = {"strong_pass": True, "strong_verified": True, "doubao_pass_at5": 0.2}
    assert is_a_bucket(rec) is True

def test_not_a_bucket_when_doubao_also_passes():
    rec = {"strong_pass": True, "strong_verified": True, "doubao_pass_at5": 0.8}
    assert is_a_bucket(rec) is False  # 饱和=易题=非燃料

def test_not_a_bucket_when_strong_unverified():
    rec = {"strong_pass": True, "strong_verified": False, "doubao_pass_at5": 0.0}
    assert is_a_bucket(rec) is None  # 强模型没真解对=无 trace 可蒸(B类/丢)

def test_build_distill_sample_shape():
    sample = build_distill_sample(
        instance_id="psf__requests-2148", problem_statement="...",
        strong_patch="diff --git ...", repo="psf/requests")
    assert sample["instruction"].strip()
    assert sample["input"].strip()        # 问题陈述 + 仓上下文
    assert sample["output"] == "diff --git ..."  # 强模型 verified 解
    assert sample["meta"]["instance_id"] == "psf__requests-2148"
```

**Step 2:** `pytest tests/test_distill_fuel.py -v` → FAIL(module 不存在)。
**Step 3:** 实现 `is_a_bucket`(三态:True/False/None·门=doubao pass@5≤0.6 阈值 + strong_verified)+ `build_distill_sample`(SFT 格式 instruction/input/output + meta)。复用 §1.3 买方口径(pass@5≤0.6)。
**Step 4:** `pytest` → PASS。
**Step 5:** commit `feat(distill): A 类 trace 判定 + SFT 样本装配纯函数`。

### Task 2:数据集累加器(幂等·去重·攒批)

**Files:**
- Modify: `phase3/backend/services/distill_fuel.py`
- Test: `phase3/backend/tests/test_distill_fuel.py`

**Step 1:写失败测试**(append A 类样本到 jsonl·按 instance_id 去重·返回累计数)

```python
def test_accumulate_dedups_by_instance(tmp_path):
    from services.distill_fuel import accumulate_sample
    p = tmp_path / "fuel.jsonl"
    n1 = accumulate_sample(str(p), {"meta": {"instance_id": "a"}, "output": "x"})
    n2 = accumulate_sample(str(p), {"meta": {"instance_id": "a"}, "output": "x2"})  # 同实例
    assert n1 == 1 and n2 == 1  # 去重·不重复累加
```

**Step 2-4:** RED → 实现 `accumulate_sample`(读现有 instance_id 集·新则 append·返回 total)→ GREEN。
**Step 5:** commit `feat(distill): A 类燃料数据集累加器(幂等去重)`。

### Task 3:FrontierSWE minting 编排(串 strong_gate→swe_verify→triage→accumulate)

**Files:**
- Create: `phase3/backend/services/distill_mint_runner.py`(effect runner·注入 seam)
- Test: `phase3/backend/tests/test_distill_mint_runner.py`

**Step 1:写失败测试**(纯编排:实例列表 → 每个跑 strong_solve_fn + verify_fn + doubao_fn → is_a_bucket → accumulate·fail-soft per 实例)

```python
def test_mint_one_batch_accumulates_only_a_bucket():
    from services.distill_mint_runner import mint_batch
    instances = ["i1", "i2"]
    def strong_fn(i): return {"patch": "diff", "ok": True}
    def verify_fn(i, patch): return {"passed": True, "ok": True}      # i1 强解 verified
    def doubao_fn(i): return {"pass_at5": 0.0 if i=="i1" else 0.8}    # i1 难倒·i2 饱和
    samples = []
    res = mint_batch(instances, strong_fn, verify_fn, doubao_fn,
                     sink=lambda s: samples.append(s))
    assert res["a_bucket"] == ["i1"] and res["rejected"] == ["i2"]
    assert len(samples) == 1
```

**Step 2-4:** RED → 实现 `mint_batch`(per 实例:strong_fn→verify_fn→doubao_fn→is_a_bucket→sink·三桶计数·fail-soft)→ GREEN。复用 `fde_triage` 三桶口径·别重写分类。
**Step 5:** commit `feat(distill): FrontierSWE A 类 minting 编排(纯·注入 seam)`。

### Task 4:接生产 seam(强模型/doubao/swe-verify 实现注入)· 🔴 GPU-gated 运行

**Files:**
- Modify: `phase3/backend/services/distill_mint_runner.py`(加 `make_*_fn` 工厂)

**Step 1:** 实现工厂(非单测·复用现成):`make_strong_fn`=百炼 qwen3.7-max completer(复用 `_run_bvh_2arm.py` 或 swe path B 的 producer)· `make_doubao_fn`=ARK doubao pass@5(复用)· `make_swe_verify_fn`=现成 `fde_bench_runner.make_swe_verify_fn`(GPU harness)。
**Step 2(gated):** cloud 上对 SWE-bench Lite 前 20 实例跑 `mint_batch` pilot → 看 A 类产率。Expected:A 类 ≥ 数道(FrontierSWE 强解率支撑)。
**Step 3:** commit `feat(distill): minting 生产 seam 注入(复用强模型/doubao/swe-verify)`。
**验证:** `fuel.jsonl` 累计真实 A 类样本数 > pilot 前。

---

## Phase 2:攒到可蒸批量(诚实定量)

**Step 2.1** 目标批量:最小信号 ~50-200 A 类 trace(s1 先例 1K 超 o1-preview 27%·但 PoC 先看信号)。
**Step 2.2** 跑 minting pass over SWE-bench Lite(300)+ Verified(待 env)→ 累计 A 类。记录真实产率(A/总)。
**Step 2.3** gate:A 类 < 50 → 扩实例源(Verified env / 其它 T4 基准 AutoLab)或诚实记"强解率不足·A 类稀"→ 调整 PoC 规模或先补燃料。**不够不硬训。**

---

## Phase 3:QLoRA 蒸馏(genuinely new · GPU-gated 运行)

**Files:**
- Create: `phase3/backend/scripts/distill_qlora.py`(训练脚本·PEFT/QLoRA)

**Step 3.1** 数据:`fuel.jsonl`(instruction/input/output)→ SFT 格式。
**Step 3.2** 基模:Qwen2.5-Coder-7B(开源·可微调·doubao 闭源不能训)。
**Step 3.3** QLoRA 配置:4-bit + LoRA adapter on A 簇 T4(`43.166.8.20`)。
**Step 3.4** 训练 + 存 adapter。验证:loss 收敛·adapter 落盘。成本 <$低两位数(设计已估)。
**Step 3.5** commit `feat(distill): QLoRA SFT 训练脚本(Qwen2.5-Coder-7B on T4)`。

---

## Phase 4:held-out 外部 benchmark eval(可证伪测量)

**Files:**
- Create: `phase3/backend/scripts/distill_eval.py`

**Step 4.1** held-out 集:训练**未见**的 A 类实例(SWE-bench 留出分片)。
**Step 4.2** 三方 pass@k:① 蒸馏后 7B(+adapter)② base 7B(无 adapter)③ doubao base。同一 swebench verifier。
**Step 4.3** 测量:蒸馏 7B pass@k vs base 7B(蒸馏增量)vs doubao(破墙判据)。
**Step 4.4** commit `feat(distill): held-out pass@k eval(蒸馏 vs base vs doubao)`。

---

## Phase 5:证或杀(决策门)

- **赢**(蒸馏 7B pass@k 显著 > base 7B·趋近/超 doubao)= 蒸馏破墙 + 飞轮因果环成立 → 放大(扩燃料/更大模型 H100/重投)。
- **平/输**(蒸馏 ≈ base)= 诚实杀"蒸馏破墙"假设 → 记 negative·回护城河副产品(B 类纯前沿仍卖钱)·不再假装飞轮自我提升。
- 落 memory(project)+ 更新北极星现状(因果环:闭/未闭 + 证据)。

---

## 并行小任务(agent 自治端 · 非 forcing function 焦点 · LINK 不 register)

**LINK string→integer 归属**(V5 实测:nautilus-prime-001=已注册 9000002·别 register 造 9000005):FDE verdict→capability 回写时把 `claimed_by` 字符串别名到整数 agent_id(nautilus-prime-001→9000002·kairos→9000003·v7→9000004),走现成 `capability_evolution.record_task_outcome`(整数键)。今天 string-keyed `platform_agent_capability_stats` 标的非依赖代码淘汰。小切片·我 turf·与中心环并行不抢焦点。

---

## 冻结(parking lot · 过分叉过滤器=0 贡献)
S3 timer · 双门 timer 启用 · 看板 · path2 claim 强制 · W2 recall uplift 见证(grounded-retrieval 类·6/14 判定撞天花板·≠蒸馏破墙·除非作"减方差提产率"辅助否则不算中心环进展)。
