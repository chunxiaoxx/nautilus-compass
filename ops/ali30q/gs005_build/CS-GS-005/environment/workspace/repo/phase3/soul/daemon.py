"""Autonomous Soul daemon · one orchestration cycle.

Order: pause → budget → goal → isolated branch → ship(apply) → pr_gate →
draft PR → track. On ANY post-branch failure: hard-reset + delete the throwaway
branch + return to master (master is NEVER touched). Draft PR is never merged.

When select_goal() returns None (no yaml goal), a SELF-IMPROVE cycle runs:
reviewer picks a target → review proposes a direction → council diverges +
converges on the best improvement → the winner description is fed to ship.
"""
from __future__ import annotations
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from soul import budget_gate, pause_check, goal_selector, pr_gate, failure_track
from soul.config import MAIN_BRANCH
from soul import reviewer, council, tools
from soul.config import (
    REPO_ROOT,
    SELF_IMPROVE_SCOPE,
    SELF_IMPROVE_EXCLUDE,
    PLATFORM_MAX_PR_DIFF_LOC,
    MAX_PR_DIFF_LOC,
    MEMORY_FILE,
)

logger = logging.getLogger("soul.daemon")


def _load_engine():
    """Lazy engine import · isolated for testability (monkeypatchable)."""
    from engine.nautilus_engine import NautilusEngine
    from engine.ship import ship
    return NautilusEngine, ship


def _run_pytest(base: str, paths: list) -> "bool | None":
    """Lazy pytest-runner call · isolated for testability (monkeypatchable)."""
    from engine.pytest_runner import run_pytest_for_changed
    return run_pytest_for_changed(base, paths)


def _make_generate_fn(engine):
    """Build a generate_fn(prompt, system) -> str backed by engine.llm.
    Monkeypatchable: tests can replace daemon._make_generate_fn.
    """
    engine._ensure_llm()
    return lambda prompt, system="": engine.llm.chat(prompt, system=system)


def select_goal_with_source() -> "tuple[dict | None, 'GoalSource | None']":
    """Slice A · daemon entry-point that returns (goal, source) tuple.

    Delegates to soul.goal_stack.next_goal() which respects the 3-source
    priority stack (P1 governance > P2 agent dispatch > P3 self-reflection).
    Existing select_goal() retained for backward compat; new cycle paths
    should use this wrapper to capture the source for outcome telemetry.

    DOUBLE-SHIP RISK: P1 source returns a peek of an accepted governance
    proposal. The L2 soul_executor.timer ALSO ships accepted proposals on
    its own 10-min cron. If a future daemon path adopts this wrapper for
    actual shipping, peek-and-claim coordination must be added to prevent
    racing. A3 only exposes the wrapper · coordination deferred to Slice B.
    """
    from soul.goal_stack import next_goal as _next_goal
    return _next_goal()


def _emit_goal_source_to_outcome(cycle_id: str, source: "object") -> None:
    """Persist goal_source on the engine_cycle_outcomes row for cycle_id.

    Slice A telemetry write · called after engine.ship() returns. Allows
    future backlog_burn_rate metric to partition cycles by source
    (P1 governance / P2 agent dispatch / P3 self-reflection).

    Fail-open: on any DB error the daemon must not crash. The metric tolerates
    NULL rows; the cycle itself is unaffected. Source is typed as object to
    avoid importing GoalSource at module level; the call site passes the enum
    value or None.

    Important: this is an UPDATE on an existing engine_cycle_outcomes row.
    The row is inserted upstream by engine.ship's outcome telemetry path
    (emit_outcome_telemetry=True). If that path failed (no row exists yet),
    this UPDATE is a no-op (0 rows affected · no error).
    """
    import os
    if source is None:
        return
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return
    # source can be a GoalSource enum (has .value) or a plain string
    source_value = getattr(source, "value", None) or str(source)
    try:
        import psycopg2
        conn = None
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()
            cur.execute(
                "UPDATE engine_cycle_outcomes SET goal_source = %s WHERE cycle_id = %s",
                (source_value, cycle_id),
            )
            conn.commit()
        finally:
            if conn is not None:
                conn.close()
    except Exception as exc:
        logger.warning("emit_goal_source failed: %s", exc)


def _mark_dispatch_shipped(dispatch_id: int, outcome: str, cycle_id: "str | None" = None) -> None:
    """Mark an agent_dispatch_log row consumed · Slice B followup.

    Stamps ship_outcome (e.g. 'shipped', 'checks_failed', 'pytest_red',
    'pr_gate_reject', 'exception') + cycle_id on the row whose id is
    *dispatch_id*. Called by run_once on both the success path (after
    pr_gate.create_draft_pr) and every abort path (so a doomed task_spec
    does NOT block the queue forever · _next_p2_agent_dispatch filters on
    ship_outcome IS NULL).

    cycle_id is optional · pass the daemon's epoch-seconds cycle_id on the
    success path (matches the row engine.ship inserted into
    engine_cycle_outcomes when ship_outcome='shipped' · satisfies the
    agent_dispatch_log.cycle_id REFERENCES engine_cycle_outcomes(cycle_id)
    FK). On abort paths leave it None · no engine_cycle_outcomes row exists
    yet (or it exists with ship_status='fail' but we did not create it from
    this code path · safer to keep dispatch.cycle_id NULL than to FK against
    a row that may move).

    Fail-open: any DB error (missing DATABASE_URL, psycopg2 import, row gone,
    column missing on a pre-followup cloud, FK miss) is logged and swallowed.
    The cycle itself stays successful; the dispatch row will be re-picked on
    the next tick but the open-PR dedup guards prevent a duplicate ship.
    """
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn or dispatch_id is None:
        return
    try:
        import psycopg2
        conn = None
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()
            cur.execute(
                "UPDATE agent_dispatch_log SET ship_outcome = %s, cycle_id = %s "
                "WHERE id = %s",
                (outcome, cycle_id, dispatch_id),
            )
            conn.commit()
        finally:
            if conn is not None:
                conn.close()
    except Exception as exc:
        logger.warning("mark_dispatch_shipped failed: %s", exc)


def _record_l4_proposal(
    pr_url: str,
    pr_number: "int | None",
    cycle_id: str,
    source_value: "str | None",
    goal_id: str,
    dispatch_id: "int | None",
) -> None:
    """L4 close-loop · record a daemon-shipped PR as a synthetic
    platform_improvement_proposals(status='executed_ok', resolved_by='soul') row
    so on_pr_merge_hook can fire the NAU settlement when a human merges the PR.

    daemon-PRs bypass L3 vote (autonomous · no governance review happened),
    but they consume the SAME L4 settlement machinery via the proposal table.
    agent_id=9000002 (V5 Nautilus Prime seed) is reused as the credited
    author until a dedicated soul agent seed exists. proposal_id format =
    `daemon-pr-{number}-{cycle_id}` so the row is greppable + idempotent on
    ON CONFLICT.

    Fail-open: missing DATABASE_URL, missing pr_url, FK miss, schema drift
    (cloud lagging behind master) all log + swallow. The cycle stays alive,
    and the PR is still mergeable manually with a manual POST to merge-callback.
    """
    import os
    import json
    if not pr_url or pr_number is None:
        return
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return
    proposal_id = f"daemon-pr-{pr_number}-{cycle_id}"
    proposed_change = json.dumps({
        "pr_url": pr_url,
        "pr_number": pr_number,
        "cycle_id": cycle_id,
        "source": source_value or "self_improve",
        "goal_id": goal_id,
        "dispatch_id": dispatch_id,
        "type": "code",
    })
    root_cause = (
        f"autonomous daemon cycle · goal: {goal_id} · "
        f"source: {source_value or 'self_improve'}"
    )
    # 9000005 = soul-autonomous-001 platform agent (5/30 seed). Distinct from
    # 9000002 (V5 nautilus-prime-001 wrapper) so daemon-shipped PRs credit the
    # soul agent's reputation/NAU and don't pollute V5 economy (anchor #2 真
    # 递归 self-improvement loop · soul earns its own NAU on merge).
    try:
        import psycopg2
        conn = None
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO platform_improvement_proposals ("
                "id, task_id, agent_id, root_cause, proposed_change, "
                "status, resolved_by, resolved_at"
                ") VALUES ("
                "%s, 9000001, 9000005, %s, %s::jsonb, "
                "'executed_ok', 'soul', NOW()"
                ") ON CONFLICT (id) DO NOTHING",
                (proposal_id, root_cause, proposed_change),
            )
            conn.commit()
            logger.info("L4 proposal recorded: %s", proposal_id)
        finally:
            if conn is not None:
                conn.close()
    except Exception as exc:
        logger.warning("record_l4_proposal failed: %s", exc)


def _parse_pr_number(pr_url: str) -> "int | None":
    """Extract the trailing numeric id from a GitHub PR url
    https://github.com/<org>/<repo>/pull/<N>. Returns None on malformed input
    so the bookkeeping helper degrades to a no-op rather than crashing."""
    if not pr_url:
        return None
    try:
        tail = pr_url.rstrip("/").rsplit("/", 1)[-1]
        return int(tail)
    except (ValueError, IndexError):
        return None


def _stamp_p2_abort(goal_id: str, source_value: "str | None", outcome: str) -> None:
    """Combined abort bookkeeping · stamps the P2 dispatch row when the goal
    came from agent_dispatch_log, else no-ops.

    Centralises the abort path so the 4 abort sites in run_once stay a single
    line each · prevents drift between sites + drop-through when adding a 5th
    abort path. Outcome strings (`checks_failed` / `pytest_red` /
    `pr_gate_reject` / `exception`) document why the row was burned without
    a PR · operator can grep for them in DB or via the audit view.
    """
    if source_value != "p2_agent_dispatch":
        return
    dispatch_id = _parse_dispatch_id(goal_id)
    if dispatch_id is None:
        return
    _mark_dispatch_shipped(dispatch_id, outcome)


def _parse_dispatch_id(goal_id: str) -> "int | None":
    """Extract the numeric row id from a goal_stack P2 id like 'dispatch-99'.

    Returns None on malformed input so the bookkeeping helper degrades to a
    no-op rather than crashing the cycle."""
    if not goal_id or not goal_id.startswith("dispatch-"):
        return None
    try:
        return int(goal_id.split("-", 1)[1])
    except (ValueError, IndexError):
        return None


def _compute_snapshot(repo: str) -> dict:
    """Capture a fitness snapshot of *repo* · ruff warning count + pytest test count.

    Returns {"ruff_warnings": int, "pytest_collect": int}. Both values default
    to 0 on any error (tool not installed, non-zero exit, output unparseable).
    Fail-open · the daemon must not crash on a missing dev tool.

    HONEST CAVEAT · this metric is a hypothesis, not a validation. A daemon
    cycle that adds a docstring typically moves neither count, so most cycles
    will show delta=0. The metric only becomes informative once we see whether
    the distribution has any positive tail at all. Operator must inspect 10+
    cycles before drawing conclusions.
    """
    snap = {"ruff_warnings": 0, "pytest_collect": 0}
    # ruff · --statistics prints a trailing 'Found N errors.' line on stderr+stdout
    try:
        res = subprocess.run(
            ["ruff", "check", "--statistics", repo],
            capture_output=True, text=True, timeout=30,
        )
        if res.returncode in (0, 1):  # ruff exits 1 when warnings found · still valid output
            import re
            m = re.search(r"Found (\d+) errors?", res.stdout or "")
            if m:
                snap["ruff_warnings"] = int(m.group(1))
    except Exception:  # noqa: BLE001 — fail-open
        pass
    # pytest · --collect-only -q prints 'N tests collected' on the last line.
    # Use sys.executable to invoke the same interpreter the daemon runs under ·
    # cloud Ubuntu typically has /usr/bin/python3 only (no `python` shim) so
    # hard-coding "python" would fail-open silently and lose the test count.
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", repo],
            capture_output=True, text=True, timeout=60,
        )
        if res.returncode in (0, 5):  # 5 = no tests collected (still valid)
            import re
            m = re.search(r"(\d+)\s+tests?\s+collected", res.stdout or "")
            if m:
                snap["pytest_collect"] = int(m.group(1))
    except Exception:  # noqa: BLE001 — fail-open
        pass
    return snap


def _fitness_delta(before: dict, after: dict) -> float:
    """Compute fitness delta · higher = better.

    Formula: (warnings_before - warnings_after) + (tests_after - tests_before)
    -> warnings going DOWN is positive, tests going UP is positive.

    Missing keys treated as 0 so partial snapshots (e.g. ruff installed,
    pytest not) still produce a comparable scalar.
    """
    wb = before.get("ruff_warnings", 0)
    wa = after.get("ruff_warnings", 0)
    tb = before.get("pytest_collect", 0)
    ta = after.get("pytest_collect", 0)
    return float((wb - wa) + (ta - tb))


def _stamp_fitness(cycle_id: str, delta: "float | None") -> None:
    """Persist fitness_delta on the engine_cycle_outcomes row.

    UPDATE-only · the row is inserted upstream by engine.ship. If the row is
    missing (e.g. ship telemetry disabled or aborted before insert) the UPDATE
    affects 0 rows · no error. Fail-open on DB error · the cycle stays
    successful · we lose the metric for this cycle but not the cycle itself.

    delta=None short-circuits · no UPDATE issued (the snapshot failed both
    sides or daemon decided not to compute · the absence of a fitness row is
    operator-meaningful, NULL is not 0).
    """
    if delta is None:
        return
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return
    try:
        import psycopg2
        conn = None
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()
            cur.execute(
                "UPDATE engine_cycle_outcomes SET fitness_delta = %s WHERE cycle_id = %s",
                (delta, cycle_id),
            )
            conn.commit()
        finally:
            if conn is not None:
                conn.close()
    except Exception as exc:
        logger.warning("stamp_fitness failed: %s", exc)


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def _diff_loc(repo: str, base: str = MAIN_BRANCH) -> int:
    """Real added+deleted line count of the cycle branch vs base (master).

    Replaces the whole-file size proxy: a MINIMAL-CHANGE edit to a large file
    produces a small diff, so the LOC cap gates the actual change, not file size.
    Fail-open to 0 on any git error (a missed cap is recoverable; the daemon
    must never crash the timer)."""
    res = _git(repo, "diff", "--numstat", base, "HEAD")
    if res.returncode != 0:
        return 0
    total = 0
    for line in res.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            for col in parts[:2]:
                if col.isdigit():
                    total += int(col)
    return total


def _abort_branch(repo: str, branch: str) -> None:
    """Undo any apply + return to master + delete the throwaway branch."""
    _git(repo, "reset", "--hard")
    _git(repo, "checkout", "master")
    _git(repo, "branch", "-D", branch)


def _goal_id_for(target: Path) -> str:
    """Self-improve goal id: selfimprove-<parent_dir>-<stem>.

    Disambiguates by parent-dir name, which is unique within the current
    SELF_IMPROVE_SCOPE globs (e.g. soul/config.py vs engine/config.py).
    """
    return f"selfimprove-{target.parent.name}-{target.stem}"


def _ship_goal(
    goal_id: str,
    task_description: str,
    engine,
    ship,
    repo: str,
    cycle_id: str,
    branch: str,
    pr_title: str,
    pr_body_extra: str,
    max_loc: int = MAX_PR_DIFF_LOC,
) -> int:
    """Shared downstream: ship → pytest gate → pr_gate → draft PR.

    Called by both the yaml-goal path and the self-improve path.
    *max_loc* lets the caller impose a stricter diff cap (platform-scope targets).
    Returns 0 on success AND on gate rejection (a rejected generation is a normal
    business outcome · systemd must not see the unit as failed), 1 only on
    infrastructure failure. Branch is cleaned up on rejection either way.
    """
    task_description = _task_prefix(goal_id) + task_description  # U17 感知+记忆注入
    result = ship(engine, task_description, repo,
                  apply=True, git_commit_msg=f"soul: {goal_id}",
                  dispatch_audit=False,
                  max_retries=1)  # U17 产能件:checks 挂带错误上下文重写一次(9/26 ruff 两连挂实证)
    budget_gate.record_cost(0.005, goal_id)

    # ship self-gates apply on checks (ship.py:160) · confirm both
    if not (result.check_result.get("passed") and result.applied):
        _log_check_failure(goal_id, result)
        _abort_branch(repo, branch)
        failure_track.record_failure(goal_id)
        _memory_append(goal_id, False, "checks_failed")
        return 0  # business outcome · circuit breaker still counts it

    # pytest gate · run tests for changed files (False = red → abort; None = no tests → proceed)
    changed = [f["path"] for f in result.files_planned]
    pytest_result = _run_pytest(repo, changed)
    if pytest_result is False:
        logger.warning("pytest gate: tests failed for goal %s · aborting", goal_id)
        _abort_branch(repo, branch)
        failure_track.record_failure(goal_id)
        _memory_append(goal_id, False, "pytest_red")
        return 0  # business outcome

    # post-apply pr_gate · reject is reversible (throwaway branch)
    ok_paths, reason = pr_gate.check_paths(changed)
    # Real diff LOC (cycle branch vs master) · NOT whole-file size proxy: a
    # MINIMAL-CHANGE edit to a large file is a small diff, so the cap gates the
    # actual change. The ship commit is already on top of master on this branch.
    total_loc = _diff_loc(repo)
    ok_loc, loc_reason = pr_gate.check_diff_loc(total_loc, max_loc)
    if not (ok_paths and ok_loc):
        logger.warning("pr_gate reject: %s %s", reason, loc_reason)
        _abort_branch(repo, branch)
        failure_track.record_failure(goal_id)
        _memory_append(goal_id, False, f"pr_gate_reject: {reason} {loc_reason}")
        return 0  # business outcome

    # no-op detection: ship applied but produced no git commit
    no_code_change = not result.git_commit
    if no_code_change:
        logger.info("no code change for goal %s (already satisfied) · mark-only PR", goal_id)

    files_line = ("NO code change (goal already satisfied) · mark-only"
                  if no_code_change else f"Files changed: {', '.join(changed)}")
    body = (
        f"Autonomous Soul cycle (cycle {cycle_id}).\n\n"
        f"{pr_body_extra}\n\n"
        f"{files_line}\n\n"
        f"Draft PR · human review + merge required (never auto-merged)."
    )
    url = pr_gate.create_draft_pr(branch, pr_title, body)
    logger.info("draft PR opened: %s", url)
    _memory_append(goal_id, True, f"PR {url}")
    _announce_pr(goal_id, url, len(changed), total_loc)  # U17 提案广播
    _ack_p2_origin(goal_id)
    failure_track.record_success()
    return 0


def _run_letter_reply(goal: dict) -> int:
    """回函型任务路径(9/20):治理裁定/征意类 → LLM 生成 VERDICT 回函 → 投函 → ack。

    与 ship(patch)路径分流:这类任务的产出是函件不是代码,塞 patch 路径
    必挂 checks(524 两连败实证,5 连败熔断会 pause soul)。"""
    goal_id = goal.get("id", "")
    spec = goal.get("task_spec", "")
    try:
        NautilusEngine, _ = _load_engine()
    except ImportError as e:
        logger.error("engine import failed for letter reply: %s", e)
        return 1
    try:
        from agent_engine.llm.client import LLMClient
        client = LLMClient()
        prompt = (
            "你是 nautilus 组织 soul 框(治理门)。以下是一封需要你裁定/回复的任务函全文:\n"
            f"=== 函件开始 ===\n{spec}\n=== 函件结束 ===\n\n"
            "要求:以 soul 治理门身份认真处理此函。若为裁定类,给出逐项裁定与理由;"
            "若为征求意见类,给出本框立场与建议。不确定处如实说不确定,不代用户拍板"
            "(涉及方向/预算/对外承诺的留给用户)。"
            "回函首行必须是 VERDICT: <一句话结论>,随后正文,总长 300-1500 字。"
            "只输出回函全文,不要其他内容。")
        reply = client.chat(prompt)
        reply = (reply or "").strip()
        if not reply or "VERDICT:" not in reply[:60]:
            logger.warning("letter reply malformed for %s (len=%d), not sent",
                           goal_id, len(reply))
            failure_track.record_failure(goal_id)
            return 0
        from datetime import datetime as _dt, timedelta as _td
        import models.agent_survival  # noqa: F401 — mapper dependency
        from models.org_mailbox import OrgMailbox
        from utils.database import SessionLocal
        s = SessionLocal()
        try:
            trace = f"{goal.get('task_spec_hash', goal_id)}-done"
            if not s.query(OrgMailbox).filter_by(trace_id=trace, to_agent="platform").first():
                s.add(OrgMailbox(from_agent="soul", to_agent="platform", trace_id=trace,
                                 title=f"[回函] {spec.splitlines()[0][:80] if spec else goal_id}",
                                 body=reply[:6000], deadline=_dt.now() + _td(hours=2),
                                 created_at=_dt.now()))
                s.commit()
                logger.info("letter reply sent for %s", goal_id)
        finally:
            s.close()
    except Exception as e:  # noqa: BLE001
        logger.warning("letter reply failed for %s: %s", goal_id, e)
        failure_track.record_failure(goal_id)
        return 0
    _ack_p2_origin(goal_id)
    failure_track.record_success()
    return 0


def _ack_p2_origin(goal_id: str) -> None:
    """P2 完工即 ack(mailbox-<id> → ack 原函)。

    9/20 卡轮根因实证:soul 开 PR 后不 ack 原函,函件永占未读任务池,
    选择器每轮重选同 goal → anti-duplicate skip → 后续任务(524/530/537)
    饿死。完工 ack 让池自然轮转。失败不阻塞(下轮 skip 分支仍在)。"""
    if not goal_id.startswith("mailbox-"):
        return
    try:
        mid = int(goal_id[len("mailbox-"):])
    except ValueError:
        return
    try:
        from datetime import datetime as _dt
        import models.agent_survival  # noqa: F401 — mapper dependency
        from models.org_mailbox import OrgMailbox
        from utils.database import SessionLocal
        s = SessionLocal()
        try:
            row = s.query(OrgMailbox).filter_by(id=mid).first()
            if row is not None and row.ack_at is None:
                row.ack_at = _dt.now()
                row.ack_note = f"soul PR shipped (goal {goal_id})"
                s.commit()
                logger.info("p2 origin letter acked: %s", goal_id)
        finally:
            s.close()
    except Exception as e:  # noqa: BLE001 — ack 失败不阻塞 ship 成功路径
        logger.warning("p2 ack failed for %s: %s", goal_id, e)


# --- U17 赋能三件(2026-09-26 用户批):感知+记忆+提案广播 ---


def _format_memory_lines(entries: list) -> str:
    """记忆条目 → 注入文本(最近 10 条,一行一轮)。纯函数可测。"""
    out = []
    for e in entries[-10:]:
        mark = "OK" if e.get("ok") else "FAIL"
        out.append(f"- {str(e.get('ts', ''))[:16]} {e.get('goal', '?')} {mark}: "
                   f"{str(e.get('note', ''))[:120]}")
    return "\n".join(out)


def _memory_load() -> list:
    try:
        return [json.loads(ln) for ln in
                MEMORY_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except Exception:  # noqa: BLE001 — 无记忆/读不出=空,不阻塞 cycle
        return []


def _memory_append(goal_id: str, ok: bool, note: str) -> None:
    """cycle 笔记落盘(untracked+.soul- 前缀 → bootstrap 硬重置免疫)。
    U19:双写 compass 组织记忆(全平台可 recall;soul 失忆重启也不丢)。"""
    try:
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with MEMORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(
                {"ts": time.strftime("%F %T"), "goal": goal_id,
                 "ok": ok, "note": note[:200]}, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        logger.warning("memory append failed: %s", e)
    try:
        tools.compass_ingest(
            name=f"soul {goal_id[-24:]} {'OK' if ok else 'FAIL'}",
            description=note[:200],
            body=f"{time.strftime('%F %T')} goal={goal_id} ok={ok} note={note}")
    except Exception:  # noqa: BLE001 — 双写失败不阻塞(本地 jsonl 已落)
        pass


def _org_context() -> str:
    """感知注入:未收函数数+待审 PR 数。失败静默(不阻塞 cycle)。"""
    parts = []
    try:
        import models.agent_survival  # noqa: F401 — mapper dependency
        from models.org_mailbox import OrgMailbox
        from utils.database import SessionLocal
        s = SessionLocal()
        try:
            n = s.query(OrgMailbox).filter_by(to_agent="soul", ack_at=None).count()
            if n:
                parts.append(f"你有 {n} 封未处理组织函件(回函型任务将被优先派发)")
        finally:
            s.close()
    except Exception:  # noqa: BLE001
        pass
    try:
        r = subprocess.run(
            ["gh", "pr", "list", "--repo", "chunxiaoxx/nautilus-core",
             "--state", "open", "--limit", "100", "--json", "headRefName",
             "--jq", '[.[] | select(.headRefName | startswith("soul/"))] | length'],
            capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip().isdigit():
            n = int(r.stdout.strip())
            if n:
                parts.append(f"soul 待审 draft PR {n} 件(积压时避免产大改)")
    except Exception:  # noqa: BLE001
        pass
    # U19 compass 全平台整合:每轮感知组织近况(红灯/阻断/进展)
    try:
        brief = tools.compass_recall("组织 红灯 阻断 进展 今日", top_k=3)
        if brief:
            parts.append("组织近况: " + " ".join(brief.split())[:240])
    except Exception:  # noqa: BLE001
        pass
    return " | ".join(parts)


def _task_prefix(goal_id: str) -> str:
    """感知+记忆前缀,拼在 ship 任务前。同目标失败史最重要——同坑不踩第二次。"""
    lines = []
    ctx = _org_context()
    if ctx:
        lines.append("[组织] " + ctx)
    fails = [m for m in _memory_load()
             if m.get("goal") == goal_id and not m.get("ok")]
    if fails:
        lines.append(f"[历史] 此目标曾失败 {len(fails)} 次: "
                     + "; ".join(str(m.get("note", ""))[:80] for m in fails[-3:])
                     + " ——换思路,勿重复同款改法")
    return ("[soul 上下文·自动注入]\n" + "\n".join(lines) + "\n\n") if lines else ""


def _announce_pr(goal_id: str, url: str, files_n: int, loc: int) -> None:
    """提案广播(交流三通道之三):开 PR 即函告 platform——评委团前身的
    透明化+值守桌面提醒。失败不阻塞 ship 成功路径。"""
    try:
        from datetime import datetime as _dt, timedelta as _td
        import models.agent_survival  # noqa: F401 — mapper dependency
        from models.org_mailbox import OrgMailbox
        from utils.database import SessionLocal
        trace = f"soul-pr-{url.rsplit('/', 1)[-1]}"
        s = SessionLocal()
        try:
            if not s.query(OrgMailbox).filter_by(trace_id=trace,
                                                 to_agent="platform").first():
                s.add(OrgMailbox(
                    from_agent="soul", to_agent="platform", trace_id=trace,
                    title=f"[soul 提案] {goal_id} · {files_n}文件/{loc}行",
                    body=(f"自改进提案已开 draft PR:{url}\n"
                          "评审走机审(PR 评论+台账)+评委团(在途);本函=值守桌面"
                          "提醒,结论以 PR 评论为准。"),
                    deadline=_dt.now() + _td(hours=2), created_at=_dt.now()))
                s.commit()
        finally:
            s.close()
    except Exception as e:  # noqa: BLE001
        logger.warning("announce failed for %s: %s", goal_id, e)


def _run_self_improve(NautilusEngine, ship, repo: str) -> int:
    """Self-improve cycle: reviewer → council → ship → PR.

    Called when select_goal() returns None.
    Returns 0 on success or graceful skip, 1 on hard failure.
    """
    soul_dir = Path(__file__).parent

    try:
        engine = NautilusEngine(base_dir=repo, dry_run=True)
    except Exception as e:  # noqa: BLE001
        logger.error("engine init failed in self-improve: %s", e)
        return 1

    try:
        generate_fn = _make_generate_fn(engine)

        target = reviewer.pick_target(
            soul_dir,
            scope_globs=SELF_IMPROVE_SCOPE,
            exclude=SELF_IMPROVE_EXCLUDE,
            repo_root=Path(repo),
        )
        if target is None:
            logger.info("self-improve: no eligible module found · skipping")
            return 0

        # Early dedup: compute goal_id from the picked target and skip BEFORE any
        # review/council LLM call (saves cost + avoids PR spam while a PR is open).
        goal_id = _goal_id_for(target)
        if pr_gate.has_open_pr_for(goal_id):
            logger.info("open PR already exists for self-improve goal %s · skipping (anti-duplicate)", goal_id)
            return 0

        rev = reviewer.review(generate_fn, target)
        if rev is None:
            logger.info("self-improve: reviewer found no improvement for %s · skipping", target.name)
            return 0

        # Read module source for council context
        try:
            context = target.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            context = ""

        # U19 全网搜索注入:提案前先看外部世界怎么做(相关修法/用法参考)
        try:
            found = tools.web_search(
                f'python {target.stem} {rev["description"][:60]}', 4)
            if found:
                context = f"{context}\n\n[外部参考·搜索]\n{found}"
        except Exception:  # noqa: BLE001
            pass

        proposals = council.propose(generate_fn, task=rev["description"], context=context)
        winner = council.converge(generate_fn, proposals, task=rev["description"])

        if not winner.get("proposal") or winner["proposal"].strip().upper() == "NONE":
            logger.info("self-improve: council found no actionable proposal for %s · skipping", target.name)
            return 0

        # U19 深度分析门:换强模型独立复审,REJECT 即弃(记入记忆,不烧熔断;
        # 复审失败=放行,不阻塞产线)
        verdict = tools.second_opinion(winner["proposal"], context)
        if verdict.startswith("REJECT"):
            logger.info("second opinion REJECT for %s: %s", goal_id, verdict[:150])
            _memory_append(goal_id, False, f"second_opinion: {verdict[:150]}")
            return 0
        if verdict:
            logger.info("second opinion APPROVE for %s", goal_id)
    except Exception as e:  # noqa: BLE001 — daemon must never crash the timer
        logger.error("self-improve pre-branch error: %s", e)
        failure_track.record_failure("selfimprove-unknown")
        return 1

    cycle_id = str(int(time.time()))
    branch = f"soul/cycle-{cycle_id}"

    r = _git(repo, "checkout", "-b", branch)
    if r.returncode != 0:
        logger.error("branch create failed: %s", r.stderr[:200])
        failure_track.record_failure(goal_id)
        return 1

    try:
        # Build an engine-friendly ship task: include the target path (so ship's
        # _inject_file_context injects the current file as ground truth) + the
        # improvement + an explicit "output the complete file" instruction.
        # Without this the engine emits prose, not file blocks (parse_error).
        try:
            target_rel = str(target.relative_to(Path(repo)))
        except ValueError:
            target_rel = str(target)
        task_description = (
            f"Apply this improvement to {target_rel}:\n\n"
            f"{winner['proposal']}\n\n"
            f"Output the COMPLETE updated {target_rel} as a single fenced code block. "
            f"Keep ALL other code identical — apply only this one improvement (MINIMAL CHANGE)."
        )
        # pr_title must match the has_open_pr_for search ("soul: <goal_id>") or
        # dedup never fires (latent bug: "self-improve" vs "selfimprove-").
        pr_title = f"soul: {goal_id}"
        pr_body_extra = (
            f"Self-improve target: {target.name}\n"
            f"Purpose: {rev.get('purpose', '')}\n\n"
            f"Winning persona: {winner.get('persona', '')}\n"
            f"Reason: {winner.get('reason', '')}\n\n"
            f"Proposal: {winner['proposal']}"
        )
        # Platform-scope (non-soul) targets get a stricter LOC cap (smaller blast radius).
        is_platform = "phase3/soul/" not in target.resolve().as_posix()
        max_loc = PLATFORM_MAX_PR_DIFF_LOC if is_platform else MAX_PR_DIFF_LOC
        return _ship_goal(
            goal_id=goal_id,
            task_description=task_description,
            engine=engine,
            ship=ship,
            repo=repo,
            cycle_id=cycle_id,
            branch=branch,
            pr_title=pr_title,
            pr_body_extra=pr_body_extra,
            max_loc=max_loc,
        )
    except Exception as e:  # noqa: BLE001
        logger.error("self-improve cycle error: %s", e)
        _abort_branch(repo, branch)
        failure_track.record_failure(goal_id)
        return 1
    finally:
        _git(repo, "checkout", "master")


def _governance_task_text(proposed_change: str) -> str:
    """Wrap an accepted governance proposal's `proposed_change` into a codegen-
    friendly ship task (W4.1 止血).

    `proposed_change` may be a JSON blob (daemon-PR self-writes, daemon.py:190)
    or a natural-language task spec (compass/V5/Kairos voted proposals). Either
    way, surface a concrete "output the complete file" instruction so the engine
    emits file blocks, not prose — mitigating the check-stage hollow
    ({'checks': []}) observed on raw NL specs. Returns '' for empty input so the
    daemon's own empty-goal handling no-ops it out (never raises).
    """
    import json
    if isinstance(proposed_change, dict):
        # upstream self-writes now store the blob natively (dict, not str);
        # serialize so the JSON-extraction path below handles it (2026-10-18 fix:
        # AttributeError crashed every daemon cycle since 10/13, mailbox stuck at 12).
        proposed_change = json.dumps(proposed_change, ensure_ascii=False)
    text = (proposed_change or "").strip()
    if not text:
        return ""
    # JSON proposals carry the actionable text in a known field · extract it so
    # the engine sees a clean instruction rather than a serialized dict.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            text = (obj.get("description") or obj.get("task")
                    or obj.get("change") or obj.get("root_cause") or text)
    except (ValueError, TypeError):
        pass
    return (
        f"Apply this accepted governance improvement to the codebase:\n\n"
        f"{text}\n\n"
        f"Output the COMPLETE updated file(s) as fenced code blocks. "
        f"Apply only this change (MINIMAL CHANGE)."
    )


def _claim_governance(proposal_id) -> bool:
    """W4.2 peek-and-claim · atomically take ownership of an accepted governance
    proposal before the daemon ships it, so soul_executor (or a concurrent
    daemon) cannot double-ship the same row.

    Flips status 'accepted' → 'claiming' for exactly one caller. Returns True if
    THIS daemon won the claim, False if the row was already claimed/shipped
    elsewhere. Fail-open: with no DATABASE_URL (test env) or a missing
    proposal_id, returns True so the existing single-process behavior is
    unchanged.
    """
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn or proposal_id is None:
        return True
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE platform_improvement_proposals "
                "SET status = 'claiming', resolved_by = 'daemon-p1' "
                "WHERE id = %s AND status = 'accepted' RETURNING id",
                (proposal_id,),
            )
            won = cur.fetchone() is not None
            conn.commit()
            return won
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 — fail-open · never crash the timer on claim
        return True


def _resolve_governance(proposal_id, status: str) -> None:
    """Resolve a claimed governance proposal: 'executed_ok' on a successful ship,
    or 'accepted' to release it back for retry on abort. No-op without a DB."""
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn or proposal_id is None:
        return
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        try:
            cur = conn.cursor()
            # Only move rows we still own (status='claiming') · do not clobber a
            # terminal state set elsewhere.
            cur.execute(
                "UPDATE platform_improvement_proposals SET status = %s "
                "WHERE id = %s AND status = 'claiming'",
                (status, proposal_id),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:  # noqa: BLE001
        return


def _log_check_failure(goal_id: str, result) -> None:
    """熔断取证(9/25):checks 失败必须留细节。

    9/24-25 五连败只有 'checks failed / not applied' 一行,无失败项名/无原文
    长度 → 无法根修的静默死亡。此后每次失败带 failed_checks/errors/raw_chars。"""
    checks = result.check_result.get("checks", [])
    failed = [c.get("name", "?") for c in checks if not c.get("passed")]
    attempts = getattr(result, "attempts", [])
    chars = [a.get("raw_response_chars") for a in attempts]
    head = (attempts[-1].get("raw_head", "") if attempts else "").replace("\n", " ")[:200]
    logger.warning(
        "checks failed / not applied for goal %s · failed_checks=%s errors=%s raw_chars=%s raw_head=%s",
        goal_id, failed or "(hollow:0 checks ran·parse 阶段无块?)",
        getattr(result, "errors", [])[:2], chars, head)


def run_once() -> int:
    # 熔断分层(9/25 用户批·#1011 承诺):pause 分两层——人工 pause 全停(人监门
    # 至上);breaker 自动熔断只断 ship 高危路径,回函/呼救通道保活。病根:9/25
    # 02:08 二次熔断后旧逻辑全停,回函通道同死 → 组织失明 17h。
    if pause_check.letters_blocked():
        logger.info("manual pause · full stop (human gate)")
        return 0
    if not budget_gate.under_cap():
        logger.info("daily budget cap reached · skipping cycle")
        return 0

    # 步0 · 开轮先收信(中枢融合条一 · 20260928 平台修)——fail-soft 双保险
    try:
        from soul import mailbox_step0
        mailbox_step0.run_step0()
    except Exception as _step0_err:  # noqa: BLE001 — 步0绝不阻断主循环
        logger.warning("mailbox_step0 failed (fail-soft): %s", _step0_err)

    # Slice B followup wire · go through the 3-source stack instead of the bare
    # yaml selector. select_goal_with_source returns (goal, source) where source
    # is one of {P1_GOVERNANCE, P2_AGENT_DISPATCH, P3_SELF_REFLECTION} or None.
    # Existing yaml goals still flow through this path via _next_p3_self_reflection
    # which delegates to goal_selector.select_goal · regression-safe.
    goal, source = select_goal_with_source()

    # No goal in any source → try self-improve path (ship 高危层,breaker 断)
    if goal is None:
        if pause_check.ship_blocked():
            logger.info("breaker pause · skipping self-improve (letters stay live)")
            return 0
        try:
            NautilusEngine, ship = _load_engine()
        except ImportError as e:
            logger.info("engine not available for self-improve · skipping: %s", e)
            return 0
        repo = str(REPO_ROOT)
        return _run_self_improve(NautilusEngine, ship, repo)

    # P2 dispatch rows carry task_spec instead of description · adapt before
    # the shared ship path (which reads goal["description"]). source.value is
    # used (vs importing GoalSource at module top) to keep this wire self-
    # contained · matches the pattern in _emit_goal_source_to_outcome.
    source_value = getattr(source, "value", None)
    if source_value == "p2_agent_dispatch":
        goal["description"] = goal.get("task_spec", "")
    elif source_value == "p1_governance":
        # P1 governance rows (goal_stack._next_p1_governance) carry
        # {id, proposal_id, proposed_change} but NO `description`. Mirror the P2
        # task_spec→description copy so the shared ship path (goal["description"])
        # does not KeyError · W4.1 止血. Wrap proposed_change in a codegen-friendly
        # task so the engine emits file blocks (not prose) · mitigates the
        # check-stage hollow ({'checks': []}) seen on raw NL specs.
        goal["description"] = _governance_task_text(goal.get("proposed_change", ""))
    # Make the source visible in the cycle log even when the goal dict didn't
    # carry one (yaml goals do, P1/P2 rows don't).
    if "source" not in goal and source_value:
        goal["source"] = source_value

    # W4.2 peek-and-claim bookkeeping · set once the daemon wins the claim (inside
    # the try, right before ship). Declared here so the finally can release a
    # claimed-but-unresolved proposal back to 'accepted' for retry.
    claimed_pid = None
    p1_resolved = False

    logger.info("selected goal: %s (source=%s)", goal.get("id"), goal.get("source"))

    # 9/20 分流:回函型任务(governance_input/discussion/oge_status/protocol_confirm)
    # 不走 ship(patch)路径——治理裁定/征意是函件产出,塞 patch 路径必挂 checks
    # (524 两连败实证,5 连败将熔断 soul)。走 LLM 生成 VERDICT 回函→投函→ack。
    if goal.get("task_type") in ("governance_input", "discussion", "oge_status",
                                 "protocol_confirm"):
        return _run_letter_reply(goal)

    # 熔断分层:ship 高危路径(patch-ship 目标)breaker/人工 pause 皆断。
    # 回函型已在上方分流保活;此处以下全是建分支/apply/PR 的高危动作。
    if pause_check.ship_blocked():
        logger.info("breaker/manual pause · skipping ship-type goal %s (letters stay live)",
                    goal.get("id"))
        return 0

    # anti-duplicate: while a cycle PR is unmerged, master's goals.yaml stays
    # pending and bootstrap reset re-selects the same goal · skip if PR open
    if pr_gate.has_open_pr_for(goal.get("id", "")):
        logger.info("open PR already exists for goal %s · skipping (anti-duplicate)", goal.get("id"))
        return 0

    try:
        NautilusEngine, ship = _load_engine()
    except ImportError as e:
        logger.error("engine import failed: %s", e)
        failure_track.record_failure(goal.get("id", "unknown"))
        _stamp_p2_abort(goal.get("id", ""), source_value, "engine_import_fail")
        return 1

    repo = str(REPO_ROOT)
    cycle_id = str(int(time.time()))
    branch = f"soul/cycle-{cycle_id}"

    r = _git(repo, "checkout", "-b", branch)
    if r.returncode != 0:
        logger.error("branch create failed: %s", r.stderr[:200])
        failure_track.record_failure(goal.get("id", "unknown"))
        _stamp_p2_abort(goal.get("id", ""), source_value, "branch_create_fail")
        return 1

    try:
        engine = NautilusEngine(base_dir=repo, dry_run=True)

        # mark goal done · commit on the cycle branch so it survives bootstrap reset
        def _mark_done_and_commit():
            if goal_selector.mark_done(goal["id"]):
                _git(repo, "add", "phase3/soul/goals.yaml")
                _git(repo, "commit", "-m", f"soul: mark {goal['id']} done")

        pr_title = f"soul: {goal['id']}"

        # W4.2 · for P1 governance goals, atomically claim the proposal before
        # shipping. If another consumer (soul_executor / concurrent daemon) already
        # claimed it, skip this cycle without shipping (no double draft PR).
        if source_value == "p1_governance":
            pid = goal.get("proposal_id")
            if _claim_governance(pid):
                claimed_pid = pid
            else:
                logger.info("gov proposal %s already claimed by another consumer · skipping", pid)
                _abort_branch(repo, branch)
                return 0

        # Fitness signal pre-snapshot · captures ruff warning count + pytest test count
        # BEFORE ship applies any changes. Cheap subprocess calls (~3-5s combined for
        # the phase3/soul scope). Fail-open · a missing tool returns 0 so the delta
        # math still works (it just may be uninformative for this cycle).
        before_snap = _compute_snapshot(repo)

        # yaml path inlines its own ship + PR logic (mark_done must precede the PR commit).
        # Slice B followup · pass the daemon's cycle_id so the engine_cycle_outcomes row
        # ship inserts shares the same key the bookkeeping helpers will later UPDATE /
        # FK against. Without this, ship generates its own YYYYMMDD_hex cycle_id and
        # _mark_dispatch_shipped's FK to engine_cycle_outcomes(cycle_id) fails.
        result = ship(engine, _task_prefix(goal.get("id", "")) + goal["description"],
                      repo,
                      apply=True, git_commit_msg=f"soul: {goal['id']}",
                      dispatch_audit=False, cycle_id=cycle_id,
                      max_retries=1)  # 同上:失败重写一次
        budget_gate.record_cost(0.005, goal.get("id", "cycle"))

        # ship self-gates apply on checks (ship.py:160) · confirm both
        if not (result.check_result.get("passed") and result.applied):
            _log_check_failure(goal.get("id"), result)
            _abort_branch(repo, branch)
            failure_track.record_failure(goal.get("id", "unknown"))
            _memory_append(goal.get("id", "unknown"), False, "checks_failed")
            _stamp_p2_abort(goal.get("id", ""), source_value, "checks_failed")
            return 0  # business outcome · circuit breaker still counts it

        # pytest gate · run tests for changed files (False = red → abort; None = no tests → proceed)
        changed = [f["path"] for f in result.files_planned]
        pytest_result = _run_pytest(repo, changed)
        if pytest_result is False:
            logger.warning("pytest gate: tests failed for goal %s · aborting", goal.get("id"))
            _abort_branch(repo, branch)
            failure_track.record_failure(goal.get("id", "unknown"))
            _stamp_p2_abort(goal.get("id", ""), source_value, "pytest_red")
            return 0  # business outcome

        # post-apply pr_gate · reject is reversible (throwaway branch)
        ok_paths, reason = pr_gate.check_paths(changed)
        total_loc = sum(f.get("size", 0) for f in result.files_planned) // 40
        ok_loc, loc_reason = pr_gate.check_diff_loc(total_loc)
        if not (ok_paths and ok_loc):
            logger.warning("pr_gate reject: %s %s", reason, loc_reason)
            _abort_branch(repo, branch)
            failure_track.record_failure(goal.get("id", "unknown"))
            _stamp_p2_abort(goal.get("id", ""), source_value, "pr_gate_reject")
            return 0  # business outcome

        # no-op detection: ship applied but produced no git commit (engine emitted
        # the file unchanged · goal already satisfied). Still mark done to advance
        # the queue; the PR records the goal as satisfied (mark-only).
        no_code_change = not result.git_commit
        if no_code_change:
            logger.info("no code change for goal %s (already satisfied) · mark-only PR", goal.get("id"))

        # 2026-09-14 修:yaml goal 的 expect_files 断言——目标文件不在 cycle 分支 HEAD
        # 即失败(治 PR #144 空活:checks 全过但交付物不存在)
        expect_files = [str(p) for p in (goal.get("expect_files") or [])]
        if expect_files:
            ok, missing = pr_gate.check_expect_files(repo, expect_files)
            if not ok:
                logger.warning("expect_files missing for %s: %s · aborting",
                               goal.get("id"), missing)
                _abort_branch(repo, branch)
                failure_track.record_failure(goal.get("id", "unknown"))
                return 0

        # mark goal done · commit on the cycle branch so it survives bootstrap reset
        _mark_done_and_commit()

        files_line = ("NO code change (goal already satisfied) · mark-only"
                      if no_code_change else f"Files changed: {', '.join(changed)}")
        body = (
            f"Autonomous Soul cycle (cycle {cycle_id}).\n\n"
            f"Goal: {goal['description']}\n\n"
            f"{files_line}\n\n"
            f"Draft PR · human review + merge required (never auto-merged)."
        )
        url = pr_gate.create_draft_pr(branch, pr_title, body)
        logger.info("draft PR opened: %s", url)

        # Slice B followup · persist goal_source on the cycle outcome row that
        # engine.ship inserted upstream (UPDATE-only · no-op if the row is
        # absent, e.g. when emit_outcome_telemetry was off). For P2 dispatch,
        # also mark the agent_dispatch_log row consumed so the next tick does
        # not re-pick it.
        _emit_goal_source_to_outcome(cycle_id, source)
        dispatch_id_for_record: "int | None" = None
        if source_value == "p2_agent_dispatch":
            dispatch_id_for_record = _parse_dispatch_id(goal.get("id", ""))
            if dispatch_id_for_record is not None:
                _mark_dispatch_shipped(dispatch_id_for_record, "shipped", cycle_id)

        # 20261003 fix·ack断链: mailbox-* goal 经 PR ship 路径完工不 ack 原函
        # (_ack_p2_origin 此前只在 letter-reply 路径调用)——队列卡最旧函每轮重选,
        # 07:07 轮 mailbox-1676 已开 PR#242 而原函未 ack 实证。此处统一补位,
        # 函数自带 mailbox- 前缀守卫,非 mailbox goal 无副作用。
        _ack_p2_origin(goal.get("id", ""))

        # L4 close-loop · synthesize a platform_improvement_proposals row so
        # on_pr_merge_hook fires the NAU settlement when a human merges this
        # PR. daemon-PRs bypass L3 vote · this synthetic row is the bridge.
        _record_l4_proposal(
            pr_url=url,
            pr_number=_parse_pr_number(url),
            cycle_id=cycle_id,
            source_value=source_value,
            goal_id=goal.get("id", ""),
            dispatch_id=dispatch_id_for_record,
        )

        # Fitness signal post-snapshot · captures the same scope POST ship-commit.
        # delta = (warnings_before - warnings_after) + (tests_after - tests_before)
        # so warnings DOWN + tests UP yields positive delta. UPDATEs engine_cycle_outcomes
        # row created upstream by engine.ship. HONEST CAVEAT: most daemon cycles will
        # show delta=0 (docstring-only changes do not move ruff/pytest counts). Operator
        # must inspect 10+ cycles before claiming the metric carries information.
        after_snap = _compute_snapshot(repo)
        _stamp_fitness(cycle_id, _fitness_delta(before_snap, after_snap))

        # W4.2 · successful P1 ship · resolve the claim to its terminal state.
        if claimed_pid is not None:
            _resolve_governance(claimed_pid, "executed_ok")
            p1_resolved = True

        failure_track.record_success()
        return 0
    except Exception as e:  # noqa: BLE001 — daemon must never crash the timer
        logger.error("cycle error: %s", e)
        _abort_branch(repo, branch)
        failure_track.record_failure(goal.get("id", "unknown"))
        _stamp_p2_abort(goal.get("id", ""), source_value, "exception")
        return 1
    finally:
        # W4.2 · release a claimed-but-unresolved proposal back to 'accepted' so an
        # aborted cycle does not strand it in 'claiming' (keeps it retryable).
        if claimed_pid is not None and not p1_resolved:
            _resolve_governance(claimed_pid, "accepted")
        _git(repo, "checkout", "master")


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    return run_once()


if __name__ == "__main__":
    sys.exit(main())
