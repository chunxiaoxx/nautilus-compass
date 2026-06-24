# compass A+B 全面提升 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. 通过 `/loop` 自定步推进(用户 2026-06-23 指定)。

**Goal:** 把 compass 从"代码完成但休眠"变成"活的、会自证价值、不再堆死机制"的分层长期记忆系统 —— 全面覆盖 a(之前规划 Phase1/2/3 + v2.3 激活)+ b(近一月 RSI+FDE 实战蒸馏 B1-B6),但**分阶段门控、不并发施工**(canonical 根因#1)。

**Architecture:** 三条原则贯穿:① **纪律先行**——先建"价值证明门 + LIVE 自省"两把刹车(B1/B2),之后每件改动都被它们门控,从根上治"堆死机制"病;② **让已有的 live 优先于建新**——Phase1 长期记忆代码全测过只差部署,先点亮它(=Goal B 本体);③ **dogfood 真痛点**——B3/B4/B5 是本 session 亲踩的 compass 自身 bug,改动小、价值高、立即受益。重活/远程 ship(timer 部署、merge main、发版、GEP 全面、耦合)全 gated-on 用户明示(STOP 铁律)。

**Tech Stack:** Python 3 stdlib(json/pathlib/re/subprocess)· pytest · systemd timer · 现有 `recall.py` / `daemon.py` / `proof/poi_calculator.py` / `scripts/tier_promotion_driver.py` / `storage/l2_distiller.py` / `drift/` / UserPromptSubmit hook。

**前置事实(2026-06-23 grounded 审计·见 memory `reference_compass_v230_plan_implemented_vs_unshipped_audit_20260623`):**
- v2.3 代码层全完成在 `feat/v2.3.0-release`(领先 main 10 commit·未合)·LIVE 仍 v2.2.0。
- Phase1 长期记忆:`promote_lifecycle_tier`+`tier_promotion_driver`+`l2_distiller` 全测过·**没部署=休眠**。
- 本 session 已做(worktree `wt/phase1-task1-reinforce`·未 merge 未部署):reinforce_on_recall_hit(cf0ddd6)+ apply_tier_weight 双路径(b919556/e7f41a8)·23 pytest 绿。
- `compass-fleet-capsule.timer` 模板**不存在**(只有 `ops/compass-daemon.service`)→ Task 需新写 .timer/.service。

---

## 🔒 门控与红线(每 Phase 执行前读)
- **STOP-ask 用户**才能做:merge 到 main / 远程 deploy timer 到 T4 / push origin / 发版 / 任何不可逆。代码+测试可自主做。
- **measurement-first**:每件 deploy 后用 Phase 0 的 LIVE 自省实测(真 timer 跑/真 tier 晋升/真 reinforce+1),不靠"应该跑"。
- **反堆机制**:Phase 3 任一项动工前,必须先通过 B1 价值证明门(答得出"它让谁在什么任务上可测变好")。答不出=defer。

## Phase 地图(排序=优先级·不并发)
| Phase | 内容 | 覆盖 | Gate | 状态 |
|---|---|---|---|---|
| 0 | B2 LIVE 自省自检 + B1 价值证明门 | b·纪律 | 无(纯本地 code) | TODO |
| 1 | 让 LLM-WIKI2 真 live(reinforce merge + tier driver timer + L2 timer + e2e) | a·Goal B 本体 | timer 部署=STOP-ask | code 部分 DONE·部署 TODO |
| 2 | B3 空转检测 + B4 跨框入站 + B5 写入矛盾检测 | b·dogfood 痛点 | 无(本地 code) | TODO |
| 3 | v2.3 发版激活 + GEP P2/P3 全面 + B6 daemon 跨框自治 + 耦合主助推 | a·Phase2/3 + b·B6 | 全 gated-on 北极星 uplift + 用户 go | DEFER |

---

## Phase 0 · 纪律基建(先做·两把刹车)

### Task 0.1: B2 — LIVE-state 自省自检(`compass doctor`)

**为什么先做**:Phase 1 部署后要用它验证"真 live 了"。它本身也治"code complete ≠ live"盲区。

**Files:**
- Create: `ops/live_state_check.py`
- Test: `tests/ops/test_live_state_check.py`

**Step 1: 写失败测试**
```python
# tests/ops/test_live_state_check.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from ops.live_state_check import check_feature_live, FEATURES

def test_features_registry_nonempty():
    # 每个被宣称的功能必须有一条 live 判据(命令+期望)
    assert len(FEATURES) >= 4
    for f in FEATURES:
        assert "name" in f and "probe" in f and "expect" in f

def test_check_reports_dormant_for_absent_timer():
    # 不存在的 systemd unit → live=False·status=dormant(不抛)
    r = check_feature_live({"name": "ghost", "probe": ["systemctl", "is-active", "ghost-xyz.timer"], "expect": "active"})
    assert r["live"] is False
    assert r["status"] in ("dormant", "error")
```

**Step 2: 跑确认失败** — `pytest tests/ops/test_live_state_check.py -v` → FAIL(no module)

**Step 3: 最小实现** `ops/live_state_check.py`:
```python
"""compass LIVE-state 自省 · 答'哪些功能在生产真跑 vs 只是 dormant code'.
NO 假装 live · 每条 probe 是可执行命令 · 输出 live/dormant/error · 永不抛."""
import subprocess

FEATURES = [
    {"name": "tier_promotion_timer",  "probe": ["systemctl", "is-active", "compass-tier-promotion.timer"], "expect": "active"},
    {"name": "l2_distill_timer",      "probe": ["systemctl", "is-active", "compass-l2-distill.timer"],      "expect": "active"},
    {"name": "daemon_reinforce",      "probe": ["grep", "-c", "COMPASS_NO_REINFORCE", "recall.py"],          "expect": ">0"},
    {"name": "daemon_tier_weight",    "probe": ["grep", "-c", "COMPASS_PROD_TIER_WEIGHT", "daemon.py"],      "expect": ">0"},
]

def check_feature_live(feature):
    try:
        out = subprocess.run(feature["probe"], capture_output=True, text=True, timeout=10)
        actual = (out.stdout or "").strip()
        exp = feature["expect"]
        if exp.startswith(">"):
            live = actual.isdigit() and int(actual) > int(exp[1:])
        else:
            live = actual == exp
        return {"name": feature["name"], "live": live,
                "status": "live" if live else "dormant", "actual": actual}
    except Exception as e:
        return {"name": feature["name"], "live": False, "status": "error", "actual": repr(e)}

def report():
    return [check_feature_live(f) for f in FEATURES]

if __name__ == "__main__":
    import json
    print(json.dumps(report(), ensure_ascii=False, indent=2))
```

**Step 4: 跑确认通过** — `pytest tests/ops/test_live_state_check.py -v` → PASS

**Step 5: 实跑一次留 baseline** — `python ops/live_state_check.py`（预期当前全 dormant=证明审计结论）

**Step 6: Commit** — `git add ops/live_state_check.py tests/ops/ && git commit -m "feat(ops): LIVE-state self-check (B2 · code-complete != live)"`

---

### Task 0.2: B1 — 价值证明门(功能准入登记)

**为什么**:每个记忆功能上线前必须绑可测 downstream uplift,否则不建=反堆机制纪律落地。复用 `proof/poi_calculator`（已有 impact 语义),不重造。

**Files:**
- Create: `proof/value_gate.py`
- Test: `tests/proof/test_value_gate.py`

**Step 1: 写失败测试**
```python
from proof.value_gate import admit_feature, ValueClaim
def test_feature_without_measurable_claim_rejected():
    errs = admit_feature(ValueClaim(name="shiny", helps_whom="", on_task="", measured_by=""))
    assert errs  # 空 claim → 拒
def test_feature_with_claim_admitted():
    errs = admit_feature(ValueClaim(name="tier_weight", helps_whom="recall consumer",
        on_task="cross-agent peer learning", measured_by="PoI cumulative_impact delta"))
    assert errs == []
```

**Step 2: 跑确认失败**

**Step 3: 实现** `proof/value_gate.py`:`ValueClaim` dataclass(name/helps_whom/on_task/measured_by)+ `admit_feature(claim)->list[str]`(四字段非空且 measured_by 引用一个真实可测信号[PoI/win_rate/recall-hit/tier-mutation]→ 准入·否则列错)。纯校验·无副作用。

**Step 4: 跑确认通过**

**Step 5: 写 `docs/FEATURE_VALUE_LEDGER.md`** —— 把已有功能逐条登记 claim(reinforce / tier_weight / OKF / GEP-P3 …),空 claim 的标 `⚠️ 待补价值证明`。

**Step 6: Commit** — `git commit -m "feat(proof): value-proof admission gate (B1 · stop building dormant mechanisms)"`

---

## Phase 1 · 让 LLM-WIKI2 真 live（Goal B 本体·最高 ROI）

> 参照既有 `docs/plans/2026-06-23-compass-phase1-longterm-memory-deploy.md`(Task0 已闭)。本 Phase = 把那份的 Task1-4 落地 + 用 Phase 0 的 doctor 验证。

### Task 1.1: merge reinforce + tier-weight 到部署源分支（STOP-ask）
- 现状:code 在 worktree `wt/phase1-task1-reinforce`(cf0ddd6/b919556/e7f41a8)·23 pytest 绿。
- **STOP-ask 用户**:merge `wt/phase1-task1-reinforce` → `feat/v2.3.0-release`?(改 LIVE recall.py + daemon.py·有 env-guard 兜底·never-breaks-recall)
- merge 后:`python ops/live_state_check.py` 确认 `daemon_reinforce`/`daemon_tier_weight` = live。

### Task 1.2: 写 tier_promotion_driver systemd unit
**Files:** Create `ops/compass-tier-promotion.service` + `ops/compass-tier-promotion.timer`(参 `ops/compass-daemon.service` 模式·User=ubuntu·ExecStart=`python3 scripts/tier_promotion_driver.py`·OnCalendar=daily)。
- Step: 写 unit → 本地 `systemd-analyze verify`(若有)→ commit `feat(ops): tier-promotion daily timer unit`。**不部署**(下 task)。

### Task 1.3: 部署 tier driver timer 到文件所在盒（STOP-ask·远程）
- **STOP-ask 用户**:部署到 T4 43.166.8.20(记忆文件 canonical 盒)?
- 部署后实测(verification-before-completion):手动 `systemctl start compass-tier-promotion.service` → 读 `tier_promotion_log.jsonl` 有真 mutation → 抽查一个 `session_*.md` 的 `tier:` 真改了 → `python ops/live_state_check.py` 确认 timer=live。
- 若 0 mutation:回查 `cumulative_impact` 是否全空(可能需先 wire reinforce 轴喂数据)。

### Task 1.4: 写 + 部署 l2_distiller nightly timer（STOP-ask·远程）
- Step1: 查 L1 overview 依赖(`l2_distiller` 读 L1 输入·若 L1 没生成先确认 l1_grouper/renderer)。
- Step2: 查盒上 ollama(`curl 127.0.0.1:11434/api/tags`)·有用 qwen2.5:7b·无则 extractive fallback。
- Step3: 写 `ops/compass-l2-distill.{service,timer}`(OnCalendar=03:00)→ commit。
- **STOP-ask 用户**部署 → 实测 `_l2/` 产摘要 + recall 能召回。

### Task 1.5: Phase1 端到端实测真 tier mutation
- 写一条胶囊 → 多次 recall 命中 → `reinforce_count` 累积 → tier driver 跑 → `tier:` 真晋升 → recall tier 加权优先返它。全链路一次跑通 + `python ops/live_state_check.py` 全 live。
- commit + 更新 `docs/FEATURE_VALUE_LEDGER.md`(reinforce/tier_weight 标 ✅ live + 实测证据)。

---

## Phase 2 · dogfood 真痛点修复（本 session 亲踩·改动小价值高）

### Task 2.1: B3 — drift daemon 无进展空转检测
**Files:** Create `drift/no_progress.py` · Test `tests/drift/test_no_progress.py`
**Step 1: 失败测试**
```python
from drift.no_progress import detect_no_progress
def test_flags_repeated_identical_output():
    hist = ["Idle·gated 无变化·等你明示信号"] * 4
    r = detect_no_progress(hist, window=3)
    assert r["stuck"] is True and r["repeats"] >= 3
def test_progress_when_output_changes():
    hist = ["did A", "did B", "did C"]
    assert detect_no_progress(hist, window=3)["stuck"] is False
```
**Step 2-3:** 实现 `detect_no_progress(recent_outputs, window=3)`：近 window 条输出近乎相同(normalized 编辑距离<阈值)且无新 tool 调用 → `{"stuck": True, "repeats": n, "hint": "你在空转·该停·surface blocker 或问用户"}`。同构 metamemory 的"无可靠 evidence"。
**Step 4-5:** 跑通 → 接进 UserPromptSubmit/Stop hook surface(渲染一行 `⚠️ no-progress: N turn 零新进展·建议停或问用户`)。
**Step 6: Commit** `feat(drift): no-progress loop detector (B3 · 本 session 踩 15 次)`

### Task 2.2: B4 — 跨框入站跨 project 可靠 surface
**Files:** Modify UserPromptSubmit hook(找 `_*TO_COMPASS_*` 的逻辑)· Test 新增
- **Step1:** grep 定位现有入站 surfacing 代码(本 session 实测:它 per-project·我在别 project 时漏了 nautilus-core 的入站)。
- **Step2: 失败测试** — 给两个 project 各放一个未读 `_OUTBOUND_*_TO_COMPASS_*`,surfacing 应两个都列(当前只列当前 project)。
- **Step3:** 改成扫所有 `Projects/*/` + `fde_t3_scratch/` 的 `_*TO_COMPASS_*`(按 mtime 排序·只列近 N 天未读)。
- **Step4-5:** 实测两 project 都 surface → commit `fix(hook): cross-project inbound surfacing (B4 · 本 session 漏一批)`。

### Task 2.3: B5 — 写入时 cross-frame 矛盾检测
**Files:** Create `proof/contradiction_check.py` · Test 新增
- **Step1: 失败测试** — 新结论 "valid_rate 0.22→0 掉" vs 近期权威入站 "valid_rate 0→0.22 涨" → flag 矛盾(数值方向相反)。
- **Step2-3:** 实现 `check_contradiction(new_claim, recent_inbound)`：对数值/方向断言做轻量矛盾检测(同实体相反方向)→ 返回 warning list(不阻止写·只 flag)。本 session 我亲踩=把方向写反。
- **Step4-5:** 跑通 → 接进 memory 写入路径(写 session_*.md 前调·有矛盾则 surface)→ commit `feat(proof): write-time cross-frame contradiction flag (B5 · 本 session 读反 valid_rate)`。

---

## Phase 3 · DEFER（gated-on 北极星 uplift + 用户 go·反堆机制)

> 动工前每项必过 B1 价值证明门。不并发。

- **v2.3 发版激活**:push release→origin + PR 合 main + PyPI tag + 激活 daemon prod 钩子(RERANK/LIFECYCLE/QUERY_REWRITE/BM25_RRF)。全 STOP-ask。
- **GEP 全面(P2/P3)**:技能图依赖边 / 复用复利×难度门 / 治理 quarantine / 负样本 forbidden_pattern。接 `2026-06-23-architecture-fusion-design.md`。gated on V5 写端。
- **B6 daemon 限权跨框自治**:Conductor/daemon 自动消费入站 + surface blocker(限权·身份红线 gated 用户)。
- **Phase3 耦合主助推 RSI**:W2 高 tier 优先 + forbidden_pattern 注入 + L2 喂 soul 蒸馏。gated on Goal A 证一次 uplift。

---

## 验证总判据(本 plan done 定义)
- **Phase 0**:`python ops/live_state_check.py` 可跑 + value_gate 拒空 claim + FEATURE_VALUE_LEDGER 建立。
- **Phase 1**:doctor 报 tier/L2 timer + reinforce + tier_weight 全 live + 端到端实测真 tier 晋升(log+文件双证)。= LLM-WIKI2 fuse 真运行。
- **Phase 2**:B3 空转检测 surface 生效 + B4 跨 project 入站不漏 + B5 矛盾 flag 生效(各带本 session 复现 case 的回归测试)。
- 全仓测试绿 + live recall 无回归。

## /loop 推进说明
用户指定 `/loop` 自定步推进。建议节奏:每 tick 推进**一个 Task**(Phase 0 → 1 → 2 顺序),deploy/merge 类 Task 到 STOP-ask 即停问用户、不擅自跨。每 tick 走 verification-before-completion 实测 + append 进展进 compass memory。Phase 3 不在 loop 自动范围(必过价值门 + 用户 go)。

关联 memory:`reference_compass_self_improvement_points_distilled_from_rsi_fde_month_20260623` · `reference_compass_v230_plan_implemented_vs_unshipped_audit_20260623` · `session_20260623_compass_capability_longterm_memory_gep_design_plan` · `canonical_rsi_fde_flywheel_consolidation_and_organic_coupling_20260623`。
</content>
