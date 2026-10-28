# F11 ship · PR #85 follow-up · engine import + branch create abort stamp gap

**写时刻**: 2026-05-30 ~16:30 CST · platform-dialog (fresh session 接 handoff #017)
**task**: F11 · 修 PR #85 follow-up · abort path cycle_id stamp gap (1 LOC daemon.py)
**真完成**: ✅ 2 LOC daemon.py + 2 TDD tests · 129/129 全 soul suite green · 0 regression
**对接**: PR #85 commit `4255401cb` (Slice B backlog-blocker fix · 4 abort path stamp)

---

## 1. F11 真 gap audit

PR #85 (commit `4255401cb` · 5/29 ship) 修了 daemon `run_once` P2 dispatch path 的 **4 abort paths** 真 stamp `_stamp_p2_abort` 防止 queue 卡死:

| line(post-fix) | abort path | outcome | PR #85 真 stamp |
|---|---|---|---|
| 689-694 | checks_failed | engine.ship check_result.passed=False | ✅ |
| 699-704 | pytest_red | pytest_runner 返 False | ✅ |
| 710-715 | pr_gate_reject | blacklisted path / LOC cap | ✅ |
| 773-778 | exception | outer try/except | ✅ |

**🔴 F11 真发现 · PR #85 漏 2 abort paths(P2 dispatch path 内 · 仍卡 queue)**:

| line | abort path | PR #85 stamp? | 真 risk |
|---|---|---|---|
| 644-649 | `_load_engine` ImportError(engine 包 missing / pip 没装) | ❌ NULL stamp | dispatch row ship_outcome=NULL · `_next_p2_agent_dispatch` 选 OLDEST NULL · queue 永远 stuck 在 doomed row(每 tick re-pick · re-fail · never marked consumed)|
| 655-659 | `_git checkout -b branch` 非 0(branch 已存在 / 磁盘满 / 权限 etc) | ❌ NULL stamp | 同 · queue 卡死 |

两条 path 共同特征:发生在 PR #85 4 abort path 之**前** · 因此 PR #85 audit 范围真没覆盖. 但 risk 模型完全一致 — PR #85 commit message 自己说:

> "Every abort path ... returned rc=1 with ship_outcome IS NULL. Since _next_p2_agent_dispatch picks the OLDEST NULL-outcome row, a single doomed task_spec would block the queue forever on every subsequent tick."

这 2 path 真满足 "every abort path" 但漏了.

---

## 2. 真 fix · 2 LOC

```diff
     try:
         NautilusEngine, ship = _load_engine()
     except ImportError as e:
         logger.error("engine import failed: %s", e)
         failure_track.record_failure(goal.get("id", "unknown"))
+        _stamp_p2_abort(goal.get("id", ""), source_value, "engine_import_fail")
         return 1

     repo = str(REPO_ROOT)
     cycle_id = str(int(time.time()))
     branch = f"soul/cycle-{cycle_id}"

     r = _git(repo, "checkout", "-b", branch)
     if r.returncode != 0:
         logger.error("branch create failed: %s", r.stderr[:200])
         failure_track.record_failure(goal.get("id", "unknown"))
+        _stamp_p2_abort(goal.get("id", ""), source_value, "branch_create_fail")
         return 1
```

`source_value` 在 line 628 上文已 set · 这 2 abort path 之前 · OK 引用.

outcome 字符串 operator-readable:
- `engine_import_fail` · 真因 engine 包 missing(pip install nautilus_engine 漏)
- `branch_create_fail` · 真因 git branch 已存在 / 磁盘满 / 权限

加 fix 后:dispatch row stamped 真 consumed · `_next_p2_agent_dispatch` 不再 re-pick · queue unblock.

---

## 3. TDD · RED → GREEN cycle 真 verified

### 3.1 RED (revert fix · 跑 test)

```
$ python3 -m pytest soul/tests/test_daemon_p2_abort_stamps.py::test_abort_on_engine_import_fail_stamps_dispatch_row \
  soul/tests/test_daemon_p2_abort_stamps.py::test_abort_on_branch_create_fail_stamps_dispatch_row -v

FAILED test_abort_on_engine_import_fail_stamps_dispatch_row
FAILED test_abort_on_branch_create_fail_stamps_dispatch_row
  AssertionError: branch_create_fail must stamp the dispatch row exactly once
  assert 0 == 1
   +  where 0 = len([])
```

真证 stamp 没 add 时 · 2 new test 真 fire fail.

### 3.2 GREEN (restore fix · 跑 full suite)

```
$ python3 -m pytest soul/tests/ -q
.........................................................                [100%]
129 passed in 2.16s
```

129/129 PASS · 5 existing PR #85 abort tests + 2 new F11 abort tests + 1 helper test + 121 其他 soul tests 全 green · 0 regression.

### 3.3 真 evidence summary

| state | new tests | full suite |
|---|---|---|
| pre-fix(revert)| 2 RED | 127/129 fail |
| post-fix(restore)| 2 GREEN | 129/129 PASS |

verification-before-completion skill iron law 真满足:Write → Run pass → Revert → MUST FAIL → Restore → Run pass.

---

## 4. 真 test 设计

### 4.1 `test_abort_on_engine_import_fail_stamps_dispatch_row`

```python
def _raise_import(*a, **k):
    raise ImportError("nautilus_engine missing")
monkeypatch.setattr(daemon, "_load_engine", _raise_import)

marked = _capture_mark(monkeypatch)
rc = daemon.run_once()
assert rc == 1
assert len(marked) == 1
did, outcome, cycle_id = marked[0]
assert did == 77
assert outcome == "engine_import_fail"
assert cycle_id is None  # no engine_cycle_outcomes row yet
```

### 4.2 `test_abort_on_branch_create_fail_stamps_dispatch_row`

选择性失败 `checkout -b` 但其他 git 调用 pass(模拟 branch already exists):

```python
real_git = daemon._git
def selective_git(repo, *args):
    if len(args) >= 2 and args[0] == "checkout" and args[1] == "-b":
        class R:
            returncode = 1
            stdout = ""
            stderr = "fatal: branch already exists"
        return R()
    return real_git(repo, *args)
monkeypatch.setattr(daemon, "_git", selective_git)
```

输出 expectations:
- rc==1 (abort 真 return 1)
- marked == [(77, "branch_create_fail", None)]
- cycle_id None(同 PR #85 design · 安全 default)

---

## 5. anchor 真审计

| anchor | F11 真贡献 |
|---|---|
| #1 agent-first | 0 直接 · 间接 = queue unblock 让真 P2 dispatch 流通(若 V5/Kairos 真 dispatch)|
| #2 产品创新 + 递归闭环 | 间接 = 防 dispatch queue 卡死 doomed row · 真 dispatch flow 保畅(handoff §1 真 L4 organic fire 0 时本 fix 价值休眠 · 但当 V5 真接 inbound 后立 active)|
| #3 反 D 维护 | +1 · 真闭一漏洞 · 防 future doomed dispatch row 卡 queue 反复消耗 cycle |
| #5 不重复造轮子 | +1 · 复用 `_stamp_p2_abort` helper(PR #85 ship) · 2 LOC 真复用 |
| #6 避免重复错误 | +1 · TDD RED-GREEN 真 verify · 不靠 "我以为 OK" |
| #7 cross-dialog turf | +1 · 0 touch V5/Kairos/compass code |

---

## 6. F11 binding-DONE 标准

- [x] gap 真 audit(§1 漏 2 abort path)
- [x] fix 真 ship(§2 2 LOC daemon.py)
- [x] TDD RED-GREEN cycle 真 verified(§3 2 RED → fix restore → 129/129 GREEN)
- [x] test 真覆盖 2 new path(§4 含 ImportError mock + selective git mock)
- [x] anchor 真审计(§5)
- [x] commit done · NOT pushed(R4 git workflow)

---

## 7. cloud sync 注意 (cross-ref F12)

PR #96 + F11 PR + F12 finding 三件 cross-ref:

- F11 fix 真 ship daemon.py 改 · merge 后 cloud `~/nautilus-soul-workspace/phase3/soul/daemon.py` 仍 OLD code(F12 finding · 无 auto sync)
- 必须用户 SSH cloud + `git fetch origin && git reset --hard origin/master` 才真生效
- F12 §5 option B (service ExecStartPre 加 git pull · 3 LOC) 真解决 sync gap
- F12.1 parking lot item · 等用户决

若 F11 PR merge 但 cloud 不 sync → cloud daemon 仍漏 stamp 2 abort path → queue 仍卡风险.

**真完整闭环**:F11 ship + F12.1 ship + 用户 SSH cloud reset · 三件都需要.

---

## 8. References

- PR #85 · commit `4255401cb` (Slice B backlog-blocker fix · 4 abort path stamp · 5/29 ship)
- daemon.py · `phase3/soul/daemon.py:644-659` (F11 修 2 LOC)
- test file · `phase3/soul/tests/test_daemon_p2_abort_stamps.py` (5/29 PR #85 ship + F11 add 2 test)
- F12 sync finding · `docs/VERIFY_F12_20260530_soul_daemon_sync_path.md`
- handoff #017 · `docs/HANDOFF_20260530_017_v5_inbound_48h_status.md`

---

**Ship by**: platform-dialog · 2026-05-30 ~16:30 CST
**R3 timer**: ~3h elapsed · within 4h budget
**4 件 act path 全 done**:F12 ✅ verify · F3 ✅→F3' verify · F5 ✅ 6 PR close (timer SSH 留用户)· F11 ✅ 2 LOC + TDD
**Next**: 报告 user 全 4 件状态 + open items (F5 timer SSH + F12.1 sync fix decision)
