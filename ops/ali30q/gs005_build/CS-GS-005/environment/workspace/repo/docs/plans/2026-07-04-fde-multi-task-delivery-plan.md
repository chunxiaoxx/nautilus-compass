# FDE 多题样例并发交付 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 7/4-7/9 增 5-50 题 grounded 入 EOVh 派活表与 S3 交付表。复用既模板与流程。

**Architecture:** `produce_50_variants.py` 模板批量派生 → `gapclosed_batch_runner.py` K 题并行 N=3 真跑 → `/api/platform/fde/verdict` 真持久化 → `submit_5tasks_to_feishu.py` 派活表真入 → S3 DLR 真送(等 fde 真接球)。

**Tech Stack:** Python 3.13 + paramiko 5.0 · H800 miniconda 3.12 + openai 2.44 + torch 2.7 · 飞书 OpenAPI · cloud: 8000 main:app FastAPI · SQLite via `services`

**设计文档:** `docs/plans/2026-07-04-fde-multi-task-delivery-design.md`(方案 C,user 拍)

---

## 现行态硬数据(7/4 22:55 UTC 锚)

| 件 | 态 |
|---|---|
| 6 题已循买方目录模板 ship | commit `1df0b9e31`/`19bc936d9`/`433ac08a6`/`da7eebd50` |
| 5 题入派活表 EOVh | commit `f2ab300c3`(5/5 row) |
| 5/5 真入 fde_verdicts | 7/4 22:20 跑 · 绑 producer 9000009 |
| producer 9000009 真注册 | wallet 0xfa7b.../api_key nau_d52871... |
| Task #0 真路径修 | commit `8b234f2fc`(/api/platform/fde/verdict) |
| Task #5 H800 daemon spec | commit `6847e3f54` · systemd 不可启真阻塞 |
| Task #31 #28 真闭环 | 等 §5 三真值齐才改 §0-GOAL |
| 已知 walrus bug | filed(`known_bug_persist_walrus_syntax_error_20260704.md`)· 不属此 plan |

---

## Task 1 · 模板批量派生(阶段 a · Robot/Quantum/ComputerSys/KernelEng 域)

**Files:**
- 复用 Create: `genopt_factory/produce_50_variants.py`
- 复用 Create: `genopt_factory/tasks/operations_research_and_decision_science/{JobShop,T SP,BinPack}/*/`
- 复用 Create: `genopt_factory/tasks/robotics_control/`(新)
- 复用 Create: `genopt_factory/tasks/quantum_information/`(扩)
- 复用 Create: `genopt_factory/tasks/computer_systems/Cache/`(扩 v2)
- Modify: `genopt_factory/PARKING_LOT.md`(注 7/4 进度)

**Step 1:** 已 grnd 验:运行 `python genopt_factory/produce_50_variants.py --domain robotics_control --variant astar` 真跑 + 看 task dir
**Step 2:** 真过 verifier 三铁律:真跑 `python genopt_factory/tools/verifier_qc.py --task-dir genopt_factory/tasks/robotics_control/PathPlan/pathplan_astar_v1_001/`
- Expected: 3 PASS(确定性 + 只读 + 60s 超时)

**Step 3:** 同模式批量派生 5 道/域 × 9 域(共 45 道)
```bash
for domain in robotics_control quantum_information optical_communication energy_systems physics_engineering; do
    for task_spec in task1 task2 task3 task4 task5; do
        python genopt_factory/produce_50_variants.py --domain $domain --variant $task_spec
        python genopt_factory/tools/verifier_qc.py --task-dir genopt_factory/tasks/$domain/$task_spec/
    done
done
```

**Step 4:** Commit:
```bash
git add genopt_factory/tasks/robotics_control/ genopt_factory/tasks/quantum_information/ genopt_factory/tasks/computer_systems/ genopt_factory/PARKING_LOT.md
git commit -m "feat(任务): 阶段 a 模板批量派生 5 道/域 × 9 域(44 道新)"
```

---

## Task 2 · driver-ssh-push N=3 真跑(阶段 b · 每题)

**Files:**
- 复用 Run: `genopt_factory/harness/genopt_orlib_run.py`(H800 端)
- 复用 Create: `genopt_factory/tasks/{domain}/{task}/gpt55_trajectory.json`

**Step 1:** 抽 1 道真跑 + 验证(JobShop la21 为例)
```bash
scp "C:/Users/chunx/Projects/nautilus-core/genopt_factory/tasks/operations_research_and_decision_science/JobShop/JobShop_la21_v2_v1_001/" \
    "cloud:/root/autodl-tmp/genopt/factory/operations_research_and_decision_science/JobShop/JobShop_la21_v2_v1_001/" -r 2>&1 | tail -2
```

**Step 2:** H800 端真跑(凭 GENOPT_GPT55_* env 已设 + driver 走 ssh-push)
```bash
ssh-paramiko / tmp / ssh / 走 Python
python -u harness/genopt_orlib_run.py \
    --task-dir factory/operations_research_and_decision_science/JobShop/JobShop_la21_v2_v1_001 \
    --n 3 --effort xhigh --timeout 900 \
    --out factory/operations_research_and_decision_science/JobShop/JobShop_la21_v2_v1_001/gpt55_trajectory_h800.json
```

**Step 3:** 真 verify + 抓 `gap_closed` + `best_score`
```bash
cat factory/.../gpt55_trajectory_h800.json | python -c "
import json,sys; d=json.load(sys.stdin)
print('seed_score', d['seed_score'], 'best', d['best_score'], 'gap', d['gap_closed'])"
```
Expected: 真值(空 算法 数)/ 100

**Step 4:** 真入 fde_verdicts(用 Task #0 修过路径)
- 调 cloud python 上 `persist5.py` 改 task_uid 与 verdict_id:
```python
vid = "h800-genopt-007-{task}-v7-{ts}-{i:02d}"
payload = {"verdict_id": vid, "task_uid": "genopt_or_jobshop_la21_v1_001_20260702", ...}
# 真 POST `/api/platform/fde/verdict` 200
```

**Step 5:** 复用 `submit_5tasks_to_feishu.py` 派活表真入(base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw`)
- Expected: 5/5 row 真入 + rec recvid 真回

**Step 6:** Commit(每 5 道一批):
```bash
git add genopt_factory/tasks/...
git commit -m "feat(任务): 阶段 b N=3 真跑 + fde_verdicts 真入 + 派活表 5/5 row 入"
```

---

## Task 3 · Conductor 双向 sync(阶段 c · 启动)

**Files:**
- Modify: `/home/ubuntu/nautilus-mvp/phase3/backend/services/conductor_runner.py`

**Step 1:** grnd 验 Conductor 真 ssh-tunnel 路径(real 真活)
```bash
ssh -o ConnectTimeout=5 cloud "systemctl is-active nautilus-conductor.timer && date && curl -s -X POST http://localhost:8000/api/agent-first/challenge -H 'Content-Type: application/json' -d '{\"capabilities\":[\"code\"]}'" 2>&1 | head -10
```

**Step 2:** 加 1 行 Conductor 配置 → 每 10min 扫 `nautilus-soul-workspace/docs/INBOUND_FROM_*_2026*.md`
```python
# 在 run_conductor_cycle (conductor_runner.py) 加:
def make_pulse_fn(components):
    def pulse(observations):
        for obs in observations:
            logger.info(f"surface inbound: {obs}")
        # 记 compass 真 inbound 真信号到 pulse output
    return pulse
```
(改 small,但真控 anchor #5 复用 — 不 autopilot)

**Step 3:** 推 cloud 端 + systemctl restart nautilus-conductor
```bash
ssh cloud "cd /home/ubuntu/nautilus-mvp/phase3/backend && \
  python -m services.conductor_runner --pulse-test 2>&1 | tail -20"
```

**Step 4:** 等 10min 真扫 + 看 Conductor log

**Step 5:** Commit local
```bash
git add services/conductor_runner.py
git commit -m "feat(conductor): 每 10min 扫 4 框 inbound 真信号(双向 sync)"
```

---

## Task 4 · (等 inbound · 阶段 c)soul 真标真接

**Files:**
- 外部: `services/fde_verdict.py` soul 真写
- 数据:已 5/5 真行 + Task 2 真入

**Step 1:** 不替 soul 真接球。等 inbound。
**Step 2:** 真 signal:
```bash
ssh cloud "psql -U nautilus -d nautilus -c 'SELECT verdict_id, external_verified FROM fde_verdicts WHERE external_verified = true LIMIT 5' 2>&1"
```
- 若真 ≥1 行 = §4 判据 1' 真闭
- 若 0 = 仍 inbound

**Step 3:** 若有真标, 推 SSOT §0-GOAL 改触发(任务 #28)。

---

## Task 5 · (等 inbound · 阶段 c)FDE runner 真起

**Files:**
- 外部: `services/fde_assignment_runner.py` + `services/fde_delivery_runner.py`

**Step 1:** 不 autopilot,等 FDE 真接球起 daemon
**Step 2:** 真 signal:
```bash
ssh cloud "ps -ef | grep fde_assignment 2>&1; tail -5 /var/log/nautilus/fde_assignment.log 2>&1"
```
- 若真运行 ≥5 道 verified = §4 判据 2 真闭
- 若 ≥5 DLR 真入 S3 = §4 判据 3 真闭

**Step 3:** 真三真值齐 = SSOT §0-GOAL 改(任务 #28 真触发)

---

## 5 硬守护栏

1. 不替对方拍 — 阶段 c 真 3 等 inbound · 0 autopilot
2. 不重造 — 复用 produce_50 / gapclosed_batch / submit_5tasks 真在模板
3. confound 先核 — 每道派生后 verifier 三铁律 + N=3 真跑后核 gap_closed
4. SSOT 钉死 — 三真值齐才改 §0-GOAL(§5 前置)
5. ship 了必验活 — 每 commit 后真跑 endpoint / curl / ssh log 真验

---

## 紧急保护

任 1 触发即回头:
- H800 ssh 失效 → 重置 askpass 脚本
- producer 9000009 被废 → 重 register 并迁移 producer 数据
- verifier bug 复现(例 Cache verifier 路径 bug 真过 5 轮调试治根)→ 走 known_bug 流程
- inbound 真接球超 14h → Conductor 真 surface + 用户拍

---

## 关联

- design `docs/plans/2026-07-04-fde-multi-task-delivery-design.md`
- buyer spec `vtf/BUYER_SPEC_GenOpt_RL_20260702.md`
- charter `FDE_BUSINESS_CHARTER.md`
- architecture `genopt_factory/ARCHITECTURE.md`
- parking `genopt_factory/PARKING_LOT.md`

— 平台 · 7/4 23:00 UTC
