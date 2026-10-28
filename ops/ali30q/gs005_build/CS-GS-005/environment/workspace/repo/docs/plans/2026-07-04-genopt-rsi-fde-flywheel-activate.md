# GenOpt RSI+FDE 内外飞轮激活 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把已有 5 周已建 nautilus 机制架构激活成运转中的内外飞轮 = 内飞轮(蒸馏)+ 外飞轮(buyer 接 FDE)+ GenOpt RL 桥接

**Architecture:** producer 真常驻(9000009 H800)= 出 N=3 真 grounded trajectory → fde_verdicts 真路径(/api/platform/fde/verdict)= 通外飞轮 · Conductor systemd 真活 10min = 内部 pulse 治精神分裂 · 5 框退化为反馈者 + 真接球节点

**Tech Stack:** paramiko (H800 SSH) · sqlite via /home/ubuntu/nautilus-mvp · systemd .timer · /api/agent-first + /api/platform/fde/verdict FastAPI 路由 · OUTBOUND 文件云端 docs/ 通道 · H800 torch 2.7+trl/peft (蒸馏)

---

## 现状硬数据(7/4 22:00 UTC · 入 plan 时已 grounded)

| 件 | 真态 |
|---|---|
| SSOT | `nautilus-core/LOOP_STATE_SSOT.md` canonical · `genopt_factory/PARKING_LOT.md` 钉死 7/2-7/9 唯一主线 |
| 卖方 | producer 真注册 agent_id=9000009 / wallet=0xfa7b...73 / api_key=nau_d52871... · 500 initial + 7d 保护 |
| 5/5 v7 trajectory | jobs 94.89 / tsp 100 / binpack 66.67 / attn 33.76 / cache 0 · 真入 /api/platform/fde/verdict |
| Conductor | `nautilus-conductor.timer` active 1 周 5 天 · 10min 心跳 · 起自 6/22 |
| H800 | 真连真活 · NVIDIA H800 PCIe 80GB · Ubuntu 22.04 · torch 2.7+cu128 · openai 2.44 |
| OPENAI 凭据 | user 拍真值 sk-c16301d1... + base_url=https://v2.qixuw.com + model=gpt-5.5 |
| §4 状态 | 1 部分闭 (5/5 verdict) · 1' external_verified=True ❌ · 2 真派 ❌ · 3 真入 DLR ❌ |

---

## Task 0 · 关害:patch persist 脚本真路径(不做则后续每次都要手 curl)

**Files:**
- Modify: `genopt_factory/tools/persist_trajectory_verdict.py:120-180` POST URL 行
- Modify: `genopt_factory/tools/register_h800_producer.py:135-160` 平台 host 默认值

**Step 1:** `grep -n "platform_url\|/api/fde/verdicts" genopt_factory/tools/persist_trajectory_verdict.py genopt_factory/tools/register_h800_producer.py`

**Step 2:** 替换 persist.py:`f"{args.platform_url}/api/platform/fde/verdict"`(原 `/api/fde/verdicts`)

**Step 3:** 替换 register.py 默认 `--platform-url`:ssh cloud `curl -s http://localhost:8000/api/agent-first/challenge` 真返回= cloud 上 ≠ localhost

**Step 4:** 跑 dry-run 验:
```bash
python genopt_factory/tools/persist_trajectory_verdict.py --task-dir genopt_factory/tasks/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001 --trajectory gpt55_trajectory_h800_v7.json --producer-agent-id 9000009 --platform-url http://localhost:8000 --dry-run
```
预期:[dry-run] would POST /api/platform/fde/verdict ✓

**Step 5:** Commit:
```bash
git add genopt_factory/tools/persist_trajectory_verdict.py genopt_factory/tools/register_h800_producer.py
git commit -m "fix(tools): 真路径 = /api/platform/fde/verdict + cloud URL 默认值(7/4 验证)"
```

---

## Task 1 · 关害:把 7/4 35 真事落 anchor-memory(防 fresh session 失忆)

**Files:**
- Modify: `~/.claude/projects/C--Users-chunx-Projects-nautilus-core/memory/MEMORY.md` 行 12-15
- 已存在:`session_20260704_5_3_judgments_real_persisted_producer9.md` 与 `session_20260704_h800_conn_grounded_openai_key_missing.md`

**Step 1:** 验证 memory 文件真已落:
```bash
ls -la ~/.claude/projects/.../memory/session_20260704_*.md
```

**Step 2:** MEMORY.md 已行 9-11 改写(7/4 5/3 judgments + H800 conn)。读现 MEMORY.md 1-20 行。

**Step 3:** Commit(若需):
```bash
git add memory/MEMORY.md memory/session_20260704*.md
git commit -m "memory(7/4): §B3 真解除 + 推断错自纠 + 5/5 verdict 真落"
```

---

## Task 2 · 激活外飞轮:FDE 真接球(等 inbound)

**Files:**
- 外部文件(FDE 框 turf): `services/fde_assignment_runner.py` 不在本框

**Step 1:** 不替对方写。等 inbound = 等 fde 接球真回。

**Step 2:** 探真信号(每 5min 一次,等真回):
```bash
ssh -o ConnectTimeout=5 cloud "ls /home/ubuntu/nautilus-soul-workspace/docs/INBOUND_FROM_FDE_*20260704* 2>/dev/null | head -5"
```

**Step 3:** 若真 inbound 来,读 + 同步到 SSOT §0-GOAL 4 表(任务 #27 / #28)

**Step 4:** 等期间每 5min 一次不动(无 ship 件,不写)。

---

## Task 3 · 激活内飞轮:soul 真 verify 标(等 inbound)

**Files:**
- 外部文件(soul-verify 框 turf): `services/fde_verdict.py` UPDATE external_verified 列
- 数据:本框已 5/5 行真 = 等 soul 真标 1 行 True 即触发关闭

**Step 1:** 等 inbound:
```bash
ssh -o ConnectTimeout=5 cloud "psql -U nautilus -d nautilus -c \"SELECT verdict_id, external_verified, external_verified_at FROM fde_verdicts WHERE external_verified = true LIMIT 5\" 2>&1 | head -10"
```

**Step 2:** 若真返回 ≥1 行 = §4 判据 1' 真闭。

**Step 3:** 同步 SSOT §0-GOAL(任务 #28)+ memory。

---

## Task 4 · 蒸馏 ready:不跑(等 V5/SWE 真产 n≥12)

**Files:**
- 外部文件(V5 框 turf): SWE 续产到 n≥12 同质料
- 本框 responsibility: 等 V5 真推 SWE A 类 + 借 GPU 不参与

**Step 1:** 不替对方跑。等 V5 真接球真推。

**Step 2:** 探测:
```bash
ssh -o ConnectTimeout=5 cloud "ls /home/ubuntu/nautilus-mvp/phase3/work_dir/aclass* 2>&1 | head -10; tail -3 /home/ubuntu/nautilus-v5/runtime/logs/latest_swebench_eval.json 2>/dev/null"
```

**Step 3:** 真 n≥12 同质料齐 = 提醒 soul-verify 跑 distill_loo --kind swe。

**Step 4:** 等期间不写不 ship。

---

## Task 5 · Conductor 扩:h800-genopt-runner 装 daemon(真常驻化)

**Files:**
- Create: `/root/autodl-tmp/genopt/systemd/h800-genopt-runner.service`
- Create: `/root/autodl-tmp/genopt/systemd/h800-genopt-runner.timer`
- Drop: H800 端 ssh 入 + 装 · (本机 driver 已在)

**Step 1:** H800 端写脚本 `/root/autodl-tmp/genopt/systemd/h800-genopt-runner.sh`:
```bash
#!/usr/bin/env bash
export PATH=/root/miniconda3/bin:$PATH
export GENOPT_GPT55_BASE_URL=https://v2.qixuw.com
export GENOPT_GPT55_API_KEY=<redacted_key_last4=c84c8>
export GENOPT_GPT55_MODEL=gpt-5.5
export NAUTILUS_AGENT_KEY=nau_d52871e733538f2a423740aeecf94200
export PRODUCER_AGENT_ID=9000009
cd /root/autodl-tmp/genopt
python -u harness/genopt_orlib_run.py \
    --task-dir factory/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001 \
    --n 3 --effort xhigh --timeout 900 \
    --out factory/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001/gpt55_trajectory_h800_daemon.json
```

**Step 2:** scp 上 H800:
```bash
scp .../h800-genopt-runner.sh cloud_jar:/root/autodl-tmp/genopt/systemd/
ssh ... "chmod +x /root/autodl-tmp/genopt/systemd/*.sh"
```

**Step 3:** 写 .service + .timer (systemd OnCalendar=*:0/30 每 30min):
```ini
[Unit]
Description=H800 GenOpt N=3 producer daemon
After=network-online.target
[Service]
Type=oneshot
ExecStart=/root/autodl-tmp/genopt/systemd/h800-genopt-runner.sh
[Install]
WantedBy=multi-user.target
```
```ini
[Unit]
Description=H800 GenOpt producer every 30min
[Timer]
OnCalendar=*:0/30
Persistent=true
[Install]
WantedBy=timers.target
```

**Step 4:** 启动 `systemctl daemon-reload && systemctl enable --now h800-genopt-runner.timer`

**Step 5:** 验证 `systemctl list-timers h800-genopt-runner*` 有触发时间

**Step 6:** Commit 到本机 repo(`genopt_factory/systemd/`)再 sync 到 cloud:
```bash
git add genopt_factory/systemd/
git commit -m "feat(systemd): h800-genopt-runner daemon 真常驻(每 30min N=3)"
```

---

## Task 6 · pulse 反馈:conductor_pulse_20260704_0730 已 ship · 持续巡检

**Files:**
- 已 ship: `conductor_pulse_20260704_0730.md` 上 cloud docs/

**Step 1:** 不写新 pulse,等 Conductor 10min 自跑(已起)

**Step 2:** 若 Conductor 真 surface 4 框 14h+ 0 真回 = 写到 SSOT 第 0 读块

**Step 3:** 等期间不发 5 轮外推。SSOT §1 钉死"不替对方拍"。

---

## Task 7 · SSOT §0-GOAL 改触发(3 真值全合时)

**Files:**
- Modify: `nautilus-core/LOOP_STATE_SSOT.md` §0-GOAL + §2 §B2/B3 + §4 判据表

**Step 1:** 等 3 真值(任务 #27/#28/#31 三 pending):
- 1':external_verified=True ≥1
- 2:fde_assignment_runner ≥5 真派 verified
- 3:fde_delivery_runner ≥5 真入 DLR

**Step 2:** 三真值齐 = 改 §0-GOAL 加 GenOpt RL 双主线 + 第 1 个真活 anchored = 真闭。

**Step 3:** 等 inbound。不替。

---

## 5 件硬守(锚 #6)

1. **不替对方拍**:5 件中 4 件是对方框 turret(V5/soul-verify/FDE/compass 接球),0 替。
2. **不重造**:Task 0 真只改路径;Task 5 真只装 daemon;其余 task 0 写。
3. **confound 先核**:每次标前 run 真 endpoint,看真返回,不下"已搞"声明。
4. **SSOT 钉死**:每次真值变 → 先改 SSOT → broadcast 4 框。
5. **ship 了必验活**:每 commit 后 真 endpoint 实测。

---

## 紧急保护 / 出 parking 触发

任 1 触发即升级:
- producer 9000009 被失效 → 重 register
- H800 ssh 密码变更 → 重新 askpass 写入
- FDE/SOUL 真接球真回 → 走 §5 §0-GOAL 改
- conductor 10min pulse 不出 → systemd 重启流程

---

## 关联

- SSOT `nautilus-core/LOOP_STATE_SSOT.md`
- 设计:`docs/plans/2026-06-22-first-resident-agent-momentum-conductor.md`
- 7/4 真态 memory:`session_20260704_5_3_judgments_real_persisted_producer9.md`
- anchor 反馈:`feedback_why_we_repeat_same_walls_four_roots_20260625`
