# 第一个常驻自治 agent · 持续推动力 Conductor 实现计划

> **For Claude:** REQUIRED SUB-SKILL: 用 executing-plans 逐任务实现。**谋定而后动·有界·反 drift·gated 与燃料并行。**

**Goal:** 给 DMAS/SOUL 第一个**活体成员**——一个常驻自治 agent(非对话框),提供**持续推动力**:跨对话框同步进展 + 回顾北极星/过往决策 + 检测停滞并推动,接替 ephemeral 对话框做不好的"连续性"角色。治多对话框同步痛 + 狗熊掰玉米(session 间失忆/失速)。

**Architecture:** cloud systemd timer 常驻服务(和 fde-janitor 同模式)。每 cycle 做**确定性**四步:① 盘点跨框状态(outbound/inbound md + contract + DB loop 态)② 对齐北极星收敛序列(7 齿轮/中心环·算当前 active 齿轮)③ 确定性检测推动动作(就绪 gated 步 / 逾期 ball / 停滞 loop / 燃料达阈)④ 持久化 pulse(写 compass 记忆 + alert + 触发就绪的**预定义**步)。用 V5 钱包-canonical 骨架出生(注册身份)+ capability LINK(挣能力)+ survival = 真 agent presence。

**Tech Stack:** Python · systemd timer · 复用 substrate:contract.py(close_loop)· compass 记忆(ingest/recall)· fde_dispatch/fde_verdict DB · capability_evolution · V5 registration.py 钱包-canonical。

## 🔴 反 drift 铁律(谋定的核心约束)
- **只做确定性检测 + surface + 触发预定义步。绝不做开放式判断/自改**(=证伪的 Probe3 self-edit 死路)。
- **判断权留给对话框/人**;agent 只提供**动量**(就绪步不让它停·ball 不让它掉·状态始终 surface)。
- 可选:用 LLM **只做状态摘要**(有界·只读)·决策全规则。
- 不发明新工作·不 ship 代码·不发公网。触发的"步"= 已存在的脚本/timer/mint(白名单)。

## 🔴 gated / 并行(反狗熊掰玉米)
- 本 plan = **谋定产物**·先写不立刻全建。真瓶颈仍是燃料(ALE)。
- conductor 跑现有 loop 无害(软燃料下=监控+同步);燃料 infra 就绪后它的"燃料达阈→触发蒸馏"才真点火。
- 与燃料线并行·不抢焦点。

---

## Phase 1:确定性纯逻辑(本地可 TDD·无 IO)

### Task 1:北极星对齐 + 齿轮态判定

**Files:** Create `phase3/backend/services/conductor_core.py` · Test `tests/test_conductor_core.py`

**Step 1 写失败测试**(给定齿轮态快照 → 算当前 active 齿轮 + 是否停滞)

```python
from services.conductor_core import active_gear, detect_stalls

def test_active_gear_is_first_incomplete_in_sequence():
    # 收敛序列 ①燃料→②LINK→③verdict→⑤记忆→⑦蒸馏
    gears = {"link": "done", "verdict": "done", "fuel": "building",
             "memory": "pending", "distill": "pending"}
    assert active_gear(gears) == "fuel"   # 第一个未完成=当前焦点

def test_detect_stalls_flags_ready_but_not_done():
    # 就绪(前置 done)却 pending 超期 = 停滞
    snap = {"gears": {"fuel": "done", "distill": "pending"},
            "distill_ready": True, "distill_idle_cycles": 5}
    stalls = detect_stalls(snap, max_idle=3)
    assert any(s["gear"] == "distill" for s in stalls)
```

**Step 2-4:** RED → 实现 `active_gear`(序列里第一个非 done)+ `detect_stalls`(就绪+超 idle=停滞)→ GREEN。
**Step 5:** commit `feat(conductor): 北极星对齐+停滞检测纯逻辑`。

### Task 2:推动动作判定(确定性·白名单)

**Step 1 写失败测试**(快照+停滞 → 推动动作列表·只白名单动作)

```python
from services.conductor_core import momentum_actions

def test_momentum_surfaces_overdue_ball_and_triggers_ready():
    snap = {"overdue_contracts": ["cnt_x"], "ready_steps": ["run_minting"],
            "fuel_count": 60, "fuel_threshold": 50}
    acts = momentum_actions(snap)
    kinds = {a["kind"] for a in acts}
    assert "surface_overdue" in kinds      # 逾期 ball → surface
    assert "trigger_ready" in kinds        # 就绪步 → 触发(白名单)
    assert "fuel_threshold_met" in kinds   # 燃料达阈 → 触发蒸馏 gate

def test_momentum_no_action_when_quiet():
    assert momentum_actions({"fuel_count": 0, "fuel_threshold": 50}) == []
```

**Step 2-5:** RED → 实现 `momentum_actions`(规则:逾期→surface·就绪→trigger(白名单 kind)·达阈→gate)→ GREEN → commit。

---

## Phase 2:effect seam(注入·gated 实跑)

### Task 3:状态盘点 + pulse 持久化(注入 IO)

**Files:** Create `phase3/backend/services/conductor_runner.py`

- `make_snapshot_fn(deps)`:读 outbound/inbound md 计数 + contract close_loop 态 + DB(settled/fuel_count/daemon health 经 HTTP)+ 齿轮态(从 compass 记忆/约定)。
- `make_pulse_fn(deps)`:写 compass 记忆 "loop pulse"(当前 active 齿轮+停滞+动作)+ alert(blocker)+ 触发白名单步。
- 编排 `run_conductor_cycle(snapshot_fn, align, actions, pulse_fn)` 纯·fail-soft per 动作。
- Test:`run_conductor_cycle` 用 stub 注入·验编排+fail-soft。
- commit。

### Task 4:身份(V5 钱包-canonical 骨架出生)· 🔴 gated 用户在场

- conductor 用 V5 `registration.py` 钱包-canonical 注册成 agent(一钱包·agents+platform_agents join)。
- verdict→capability LINK 已接(它挣 "conductor:momentum" capability)。survival 记录。
- 红线 gated(注册=链上动作·用户在场)。

---

## Phase 3:systemd 部署(常驻)· 🔴 gated cloud

- `nautilus-conductor.service` + `.timer`(每 N min·和 fde-janitor 同模式)·run.sh。
- 部署 cloud(外科·非对话框)。验证:timer active·pulse 写进 compass 记忆·第一个 cycle 真盘点真 surface。
- **= DMAS/SOUL 第一个活体常驻成员上线(铁证:ps 有 conductor 进程·compass 记忆有 pulse)。**

---

## 验收(反 facade)
- conductor 进程常驻(ps 可见·非对话框)。
- 每 cycle 写真 pulse 到 compass 记忆(下个对话框 session 一开就读到当前状态=连续性)。
- 逾期 ball/就绪步/燃料达阈 真被 surface/触发(实测一例)。
- 它有注册身份 + capability + survival(真 agent 非 cron)。

## 冻结(parking·过分叉过滤器)
多 agent mesh 扩展(verifier/curator 各做 daemon)= conductor 证明价值后再说。开放式 LLM 编排 = 永不(drift)。
