# F12 verify · Soul daemon sync 路径 audit

**写时刻**: 2026-05-30 ~15:00 CST · platform-dialog (fresh session 接 handoff #017)
**task**: F12 · verify-deployment 验 Soul daemon sync 路径(防 PR #96 merge 不生效)
**前置**: handoff #017 · PR #96 OPEN draft · `inc3-fitness-gap1-self-improve-hook` → master
**结论**: 🔴 **sync 路径 gap confirmed · PR #96 merge ≠ cloud Soul daemon 真生效**

---

## 1. F12 scope · 真要 verify 的是啥

handoff #017 §3.3 显示 5/30 daemon timer 5 次 fire 真 ship PR(#92 #93 #95 #97).
PR #96 修的是 `phase3/soul/daemon.py:_ship_goal` 加 `_stamp_fitness` hook
(fix self-improve path bypass fitness 问题 · before/after snapshot + ruff/pytest delta).

**问题**: 当 PR #96 merge 到 master 后 · cloud Soul daemon 是否会自动用新 code?

anchor #6 反 anti-pattern "看 systemctl active 就当 deploy OK"(drift score=+0.042 此 session 已 flag) · 不假设 merge ⇒ effective.

---

## 2. Evidence · sync 路径每一段 audit

### 2.1 `phase3/scripts/sync-agent-engine.sh` · NOT cover soul/

读全文(41 行):

```bash
SRC="$BASE_DIR/agent-engine"
DST="$BASE_DIR/backend/agent_engine"

for subdir in executors bootstrap core; do
    ...cp -r "$SRC/$subdir/"* "$DST/$subdir/"
done

# top-level .py files
cp "$SRC/"*.py "$DST/" 2>/dev/null || true
```

**真发现**: sync script 只覆盖 `phase3/agent-engine/` → `phase3/backend/agent_engine/`. **NOT** sync `phase3/soul/`. PR #96 修的是 `phase3/soul/daemon.py` · 此路径完全不在 sync script scope.

### 2.2 `nautilus-soul.service` · NOT pre-pull

读全文(14 行):

```ini
[Service]
Type=oneshot
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/nautilus-soul-workspace/phase3
EnvironmentFile=/home/ubuntu/nautilus-soul-workspace/.soul-env
ExecStart=/usr/bin/python3 -m soul.daemon
```

**真发现**: **NO `ExecStartPre`**. systemd timer 每 2h fire 时直接跑 daemon · 不 git pull. 假定 working tree 已是 latest.

### 2.3 `nautilus-soul.timer` · 单纯 schedule

```ini
[Timer]
OnBootSec=10min
OnUnitActiveSec=2h
Persistent=true
```

**真发现**: 单纯定时 · 无 pre-hook.

### 2.4 `phase3/soul/daemon.py` · NO origin pull

```
$ grep -n "git pull\|git fetch\|origin/master" phase3/soul/daemon.py
(no matches)

$ grep -n "subprocess\|git " phase3/soul/daemon.py | head
13:import subprocess
292:    res = subprocess.run(  # ruff snapshot (NOT git)
308:    res = subprocess.run(  # pytest snapshot (NOT git)
374:def _git(repo, *args): return subprocess.run(["git", "-C", repo, *args], ...)
398:def _abort_branch(repo, branch):
400:    _git(repo, "reset", "--hard")
401:    _git(repo, "checkout", "master")   # LOCAL master · NOT origin/master
402:    _git(repo, "branch", "-D", branch)
561:    r = _git(repo, "checkout", "-b", branch)  # cycle branch off LOCAL master
```

**真发现**:
- daemon.py 所有 git ops 都 LOCAL · `checkout master` (line 401) 是 local master · 不 `pull origin master`
- `_abort_branch` 重置到 local master state(line 400-401)· local master = 上次 bootstrap 时 snapshot
- 全文件 0 `pull` / 0 `fetch` / 0 `origin/master` match

### 2.5 `phase3/soul/bootstrap.sh` · 唯一有 reset --hard origin/master

```bash
git fetch origin master       # line 13
git reset --hard origin/master  # line 18
```

**真发现**: 这是**唯一**能让 cloud workspace 真同步 origin/master 的命令. 但 bootstrap.sh:
- 只在初始化/手动 re-run 时跑
- 不在 systemd / cron / daemon 内任何调用链

### 2.6 phase3/soul/ 全目录 grep · 确认 0 auto-sync

```
$ grep -rn "git pull\|git fetch\|origin/master" phase3/soul/
phase3/soul/bootstrap.sh:13:    git fetch origin master
phase3/soul/bootstrap.sh:18:    git reset --hard origin/master
(only matches · 0 daemon/service/timer touches origin)
```

### 2.7 PR #96 真状态

```json
{"baseRefName":"master","headRefName":"inc3-fitness-gap1-self-improve-hook",
 "mergeable":"MERGEABLE","mergedAt":null,"number":96,"state":"OPEN"}
```

OPEN draft · 还没 merge. F12 是 preventive verify.

---

## 3. 真结论 · sync gap confirmed

| 路径 | 是否 auto-sync origin/master? | 触发条件 |
|---|---|---|
| `soul.daemon` Python | ❌ | 0 git pull/fetch |
| `nautilus-soul.service` | ❌ | NO `ExecStartPre` |
| `nautilus-soul.timer` | ❌ | 单纯 schedule |
| `sync-agent-engine.sh` | ❌ | 只 cover `agent-engine/` · NOT `soul/` |
| `bootstrap.sh` | ✅(唯一)| **手动 re-run** · 不在任何自动链 |

**真状态**: cloud `~/nautilus-soul-workspace` 的 `phase3/soul/daemon.py` = 上次手动 bootstrap 或 git reset 时的 snapshot. PR #96 merge 到 GitHub master 后 cloud daemon **不会自动用新 code**.

---

## 4. 含义 · 为啥 5/30 daemon 仍能 ship PR

handoff #017 §3.1 显示 5/30 daemon 5 次 fire 真 ship PR(#92 #93 #95 #97)= **不矛盾** 上面 finding · 因为:

- daemon 工作流: `checkout -b cycle-branch` off local master → apply changes → push branch 到 origin → create draft PR via GH API
- draft PR 的 base 是 **origin/master**(GH 那边自动 latest)· 不是 local master
- 所以 cycle branch push + PR create 都正常
- 但 cycle branch 的 commits 是基于 **local master snapshot**(可能落后 origin/master 若 cloud 没 sync)

**真问题**:
1. 若 cloud local master 是 5/29 evening snapshot · 5/30 fire 用的 daemon.py 是 5/29 evening 的 version(无 PR #96 的 fitness hook)
2. handoff #017 §3.2 fitness_delta=NULL 真根因诊断 confirm self-improve path bypass fitness hook · 这是用 5/29 version 跑的(因为 PR #96 5/30 才 ship 还没 merge)
3. PR #96 merge 后,**必须手动** SSH cloud 跑 `cd ~/nautilus-soul-workspace && git fetch origin && git reset --hard origin/master` · 否则下次 fire 仍用 old code · fitness_delta 仍 NULL

---

## 5. Mitigation 选项

**选项 A · 手动 ack 路径 · 0 LOC**
- PR #96 merge 后人 SSH cloud 跑 `git reset --hard origin/master`
- 优:0 code change · 维护简单
- 劣:每次 master 更新都要人触发 · anchor #6 反 "靠人提醒" 复发风险

**选项 B · service ExecStartPre 加 git pull · 3 LOC**
```ini
ExecStartPre=/usr/bin/git -C /home/ubuntu/nautilus-soul-workspace fetch origin master
ExecStartPre=/usr/bin/git -C /home/ubuntu/nautilus-soul-workspace reset --hard origin/master
ExecStart=/usr/bin/python3 -m soul.daemon
```
- 优:每次 timer fire 都自动 sync · 0 人工干预
- 劣:若 daemon 跑一半挂了 · 下次 fire reset --hard 会丢任何未 push 的 cycle commit(其实 cycle commits 已 push 到 origin · safe)
- 真权衡:`reset --hard origin/master` 是 destructive · 但 daemon 设计就是 "master is NEVER touched"(daemon.py:5)所以 reset 安全

**选项 C · 独立 cron job 每小时 git pull · 12-15 LOC**
- 新建 `nautilus-soul-sync.service` + `.timer` · 1h 跑 `git reset --hard origin/master`
- 优:独立 service · daemon 自身不变
- 劣:多一个 service 维护

**推荐 = 选项 B**:
- 真最低 LOC(3 行) · 真最低维护(只改 .service unit)· 反 D 维护陷阱 anchor #3
- destructive 操作 daemon 自身设计已 assume(master never touched)· 与现有契约一致
- 自动机制 vs 自律(anchor #6 真 fix)

---

## 6. F12 binding-DONE 标准

- [x] sync 路径每段 audit(2.1-2.6)
- [x] PR #96 真状态 confirm(2.7)
- [x] 真 evidence 写下(grep/read 输出)
- [x] sync gap 真结论(§3 table)
- [x] 5/30 daemon 能 fire 的真原因 reconcile(§4)
- [x] mitigation 选项列 + 推荐(§5)
- [ ] 选项 B 真 ship(留 user 决:F12 binding 结 · 或 F12 内续 ship 选 B)

---

## 7. References

- handoff #017 · `docs/HANDOFF_20260530_017_v5_inbound_48h_status.md`
- PR #96 · https://github.com/chunxiaoxx/nautilus-core/pull/96
- daemon.py · `phase3/soul/daemon.py` (line 5 master-never-touched contract · line 414-498 _ship_goal+fitness hook)
- bootstrap.sh · `phase3/soul/bootstrap.sh`
- systemd · `phase3/soul/systemd/nautilus-soul.{service,timer}`
- sync script · `phase3/scripts/sync-agent-engine.sh`(NOT cover soul/)
- anchor #6 · `memory/anchor_anti_patterns_history.md`(看 systemctl active 就当 deploy OK)
- 5/27 session · DeepSeek provider 也撞过 sync 路径(`agent-engine/llm/client.py` 必改源 因 sync 覆写)

---

**Verify by**: platform-dialog · 2026-05-30 ~15:00 CST
**R3 timer**: ~1h elapsed · within 4h budget
**Next**: user 决 → option B ship in F12 内 / 留 F3 后单独 PR / F12 done 直进 F3
