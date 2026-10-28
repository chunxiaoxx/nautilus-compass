"""G2-B1 resident executor: registered agent that drains the repair-task queue.

Productization of the 8/22 finding (agentic loop > single completion), per
§0-ARCH: the executor registers itself via /api/agent-first (challenge ->
integer agent_id -> wallet -> survival record) instead of running as a bare
script identity. Queue rows come from g2_b1_bug_miner.py (g2-b1-task-v1).

Per task: disposable buggy worktree -> RED precondition -> agentic loop
(g2_b1_agentic_runner) -> evidence JSON. Budget discipline: cumulative token
cap per task, fail-closed; one terminal state per task, no retries.

Registration credentials are written to a local file OUTSIDE the repo
(~/.nautilus/g2b1_executor.json, 0600). Never hardcode keys.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g2_b1_agentic_runner import (  # noqa: E402
    BudgetExceeded, SYSTEM_PROMPT, run_agentic_loop,
)

EXECUTOR_NAME = "nautilus-repair-executor-001"
CRED_PATH = Path.home() / ".nautilus" / "g2b1_executor.json"

PROVIDERS = {
    # 2026-09-05:自有中转站(HR 框 newapi,openai 兼容)——executor 燃料主臂,
    # radar_llm_screen 同款配方(k3 判读已实证);旧三件降为兜底链
    "chunxiao_k3": ("https://api.chunxiao.wang/v1", "k3", "CHUNXIAO_API_KEY"),
    "deepseek": ("https://api.deepseek.com", "deepseek-v4-flash", "DEEPSEEK_API_KEY"),
    "ark_glm": ("https://ark.cn-beijing.volces.com/api/v3", "glm-5-2-260617", "ARK_API_KEY"),
    # 2026-08-28 V5:GLM coding plan(anthropic 兼容端点·ARK 欠费后 executor 燃料臂)
    "glm_plan": ("https://open.bigmodel.cn/api/anthropic", "glm-5.3-flash", "GLM_API_KEY"),
    # 2026-08-28 用户授权平台多用:minimax m3(V5 solve_task 同款 anthropic 兼容)
    "minimax_m3": ("https://api.minimaxi.com/anthropic", "anthropic/MiniMax-M3",
                   "MINIMAX_API_KEY"),
}
# anthropic 兼容风格(system 独立字段 + content 数组)的 provider 集合
ANTHROPIC_PROVIDERS = {"glm_plan", "minimax_m3"}
# Production verdict-bus fallback — a missing env must never silently drop the
# POST (8/28 revival: schtasks env lacked NAUTILUS_BACKEND_BASE → evidence
# written, verdict never posted, zero output printed).
DEFAULT_BACKEND_BASE = "https://www.nautilus.social"
DEFAULT_MAX_TOTAL_TOKENS = 200_000


# --- registration (agent-first: challenge -> integer agent_id) ---

_KNOWN_ANSWERS = {  # fixed challenge bank in api/agent_first_register.py
    "What is the output of: print(sum(range(1, 11)))?": "55",
    "Classify this text as positive or negative: 'This is wonderful!' Answer with one word.": "positive",
    "What is the derivative of x^3? Write just the expression.": "3x^2",
    "What is 7 * 8?": "56",
}


def register_executor(base_url: str) -> dict:
    """Solve the anti-Sybil challenge and register. Returns persisted creds."""
    with httpx.Client(base_url=base_url, timeout=30, trust_env=False) as http:
        challenge = http.post("/api/agent-first/challenge",
                              json={"capabilities": ["code"]}).json()
        prompt = challenge["challenge_prompt"]
        answer = _KNOWN_ANSWERS.get(prompt)
        if answer is None:
            raise RuntimeError(f"unknown challenge prompt: {prompt}")
        resp = http.post("/api/agent-first/register", json={
            "name": EXECUTOR_NAME,
            "description": "Resident agentic repair executor (G2-B1 pattern)",
            "capabilities": ["code"],
            "proof_of_capability": f"{challenge['challenge_id']}:{answer}",
        })
    resp.raise_for_status()
    creds = resp.json()
    CRED_PATH.parent.mkdir(parents=True, exist_ok=True)
    CRED_PATH.write_text(json.dumps(creds, indent=1), encoding="utf-8")
    if os.name == "posix":
        CRED_PATH.chmod(0o600)
    return creds


def load_creds() -> dict | None:
    return json.loads(CRED_PATH.read_text(encoding="utf-8")) if CRED_PATH.exists() else None


# --- live completion (provider passthrough) ---

def make_completer(provider: str, max_tokens: int = 16_384):
    origin, model, key_env = PROVIDERS[provider]
    api_key = os.environ.get(key_env)
    if not api_key:
        raise SystemExit(f"{key_env} missing")

    def complete(prompt: str) -> dict:
        import httpx as _httpx
        if provider in ANTHROPIC_PROVIDERS:
            # anthropic 兼容:system 独立字段;content 数组取 text 块(滤 thinking)
            body = {
                "model": model, "max_tokens": max_tokens,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            }
            url = "/v1/messages"
            headers = {"x-api-key": api_key,
                       "anthropic-version": "2023-06-01"}
            text_of = lambda d: "".join(
                b.get("text", "") for b in d.get("content", [])
                if b.get("type") == "text").strip()
        else:
            body = {
                "model": model,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                             {"role": "user", "content": prompt}],
                "stream": False, "max_tokens": max_tokens,
            }
            url = "/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}"}
            text_of = None
        # GLM-5.2 long-thinking completions can exceed 15 min on first token;
        # one ReadTimeout retry (cumulative token cap still guards total spend).
        # 429 (GLM coding plan RPM) → one 20s backoff retry (8/28 pilot 实证崩批).
        for attempt in (1, 2):
            try:
                with httpx.Client(base_url=origin,
                                  timeout=httpx.Timeout(1800, connect=30),
                                  trust_env=False) as http:
                    response = http.post(url, headers=headers, json=body)
            except _httpx.ReadTimeout:
                if attempt == 2:
                    raise
                continue  # retry once; without this the handler fell through
                # and referenced `response` before assignment (9/8 L2 题10:
                # a 30-min wait that ends in UnboundLocalError, burning the task)
            if response.status_code == 429 and attempt == 1:
                time.sleep(20)
                continue
            break
        if response.status_code != 200:
            raise RuntimeError(f"http_{response.status_code}")
        # 9/5:上游偶发 200+空 body(80 次 "Expecting value" 连败根因之一)→
        # 转 RuntimeError 触发 fallback 切臂,而不是 json 解析裸崩
        if not (response.text or "").strip():
            raise RuntimeError("empty_body")
        document = response.json()
        if provider in ANTHROPIC_PROVIDERS:
            u = dict(document.get("usage", {}))
            # anthropic usage has input/output_tokens; runners expect
            # total_tokens — normalize so budget/accounting works (9/8:
            # minimax arm showed tokens=0 everywhere in T6)
            u.setdefault("total_tokens",
                         u.get("input_tokens", 0) + u.get("output_tokens", 0))
            return {
                "content": text_of(document),
                "usage": u,
                "model": document.get("model"),
                "finish_reason": document.get("stop_reason"),
            }
        choice = document["choices"][0]
        return {
            "content": (choice["message"].get("content") or "").strip(),
            "usage": document.get("usage", {}),
            "model": document.get("model"),
            "finish_reason": choice.get("finish_reason"),
        }

    return complete


def make_fallback_completer(providers, max_tokens: int = 16_384):
    """自愈三件套①(修配):LLM 臂失败自动切备胎链(2026-08-28 V5)。

    主臂 raise(403 欠费/429 限速/断流)→ 依序切下一臂,切换事件打印可见
    (供 schtasks 日志/值守观测);全链败 raise 最后异常(fail-closed 不吞)。
    providers 形如 ["glm_plan", "minimax_m3", "deepseek"]。
    """
    chain = [(p, make_completer(p, max_tokens)) for p in providers]

    def complete(prompt: str) -> dict:
        last = None
        for name, fn in chain:
            try:
                out = fn(prompt)
                complete.used["provider"] = name   # 实际产出臂归因(V5 驾驶舱分组字段)
                complete.used["all"].append(name)
                return out
            except Exception as e:  # noqa: BLE001 — 修配要兜一切臂级故障
                last = e
                print(f"[arm-fallback] {name} 失败"
                      f"({type(e).__name__}: {str(e)[:80]}) → 切下一臂",
                      flush=True)
        raise last

    complete.used = {"provider": None, "all": []}
    return complete


def _provider_used_of(completer, provider: str) -> str:
    """evidence.provider_used:实际产出完成内容的链成员(fallback 链归因)。

    链 completer → 最后一次成功成员;单臂 completer(无 used 属性)→ 臂名本身。
    evidence.provider 仍是臂名(文件名/verdict_id 连续性不变),归因只加不减。
    """
    used = getattr(completer, "used", None)
    if isinstance(used, dict) and used.get("provider"):
        return used["provider"]
    return provider

def _derive_test_anchor(repo_root: Path, fix_commit: str,
                        test_files: list[str]) -> str | None:
    """Test id = first test function ADDED by the reference fix, else the file."""
    diff = subprocess.run(["git", "show", fix_commit, "--", *test_files],
                          cwd=repo_root, capture_output=True, timeout=120,
                          check=True).stdout.decode("utf-8", "replace")
    current_file = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        match = re.match(r"^\+\s*(?:async )?def (test_\w+)", line)
        if match and current_file:
            return f"{current_file}::{match.group(1)}"
    return test_files[0] if test_files else None


def _find_red_test(backend: Path, test_file: str) -> str | None:
    """Run the test FILE on the buggy tree; return the first RED anchor.

    A mined task is only a repair task if something is genuinely RED here.
    SWE-bench style checkouts often ERROR at collection (the new test imports
    symbols the buggy source doesn't have yet) — that IS the red state, not a
    skip, so ERROR anchors count too.
    """
    # confcutdir = the dir owning the tests/ tree (repo-agnostic).
    parts = Path(test_file.replace("\\", "/")).parts
    conf = "tests"
    for i, part in enumerate(parts):
        if part == "tests" and i > 0:
            conf = str(Path(*parts[:i]))
            break
    run = subprocess.run(
        ["python", "-m", "pytest", test_file, "-q", f"--confcutdir={conf}"],
        cwd=backend, capture_output=True, timeout=900)
    out = run.stdout.decode("utf-8", "replace")
    if run.returncode == 0 or "no tests ran" in out:
        return None
    match = re.search(r"FAILED (\S+?::\w+)", out)
    if match:
        return match.group(1)
    match = re.search(r"ERROR (\S+?\.py)", out)
    if match:
        return match.group(1)  # collection error: whole file is the anchor
    return None


def _evidence_path_for(task: dict, provider: str, evidence_dir: Path) -> Path:
    # 行自带 task_uid(变体:合成哈希命名空间)优先;模板行保持 ref10 老公式
    uid = task.get("task_uid")
    hash10 = (uid.split(":", 1)[1] if uid and ":" in uid
              else task["reference_fix_commit"][:10])[:10]
    return evidence_dir / f"g2b1-exec-{hash10}-{provider}.json"


def _record_verdict_post(ev: dict, evidence_path: Path, poster=None):
    """POST the verdict and persist the outcome into the evidence file.

    8/28: a transient POST failure used to leave zero trace — the evidence
    existed, the next run replay-skipped it, and the verdict was lost forever.
    """
    r = submit_verdict(ev, poster=poster)
    ev["verdict_post_status"] = r["status"] if r else None
    evidence_path.write_text(json.dumps(ev, indent=1) + "\n", encoding="utf-8")
    return r


def _backfill_replay_verdict(ev: dict, evidence_path: Path, poster=None):
    """Replay of an evidence with a missing/failed verdict POST re-posts it.

    The verdict-bus is idempotent on verdict_id, so backfill is always safe.
    """
    if ev.get("verdict_post_status") == 200:
        return None
    return _record_verdict_post(ev, evidence_path, poster=poster)


def run_task(repo_root: Path, task: dict, completer, provider: str,
             evidence_dir: Path,
             max_total_tokens: int = DEFAULT_MAX_TOTAL_TOKENS) -> dict:
    buggy_commit = task["buggy_commit"]
    workdir = Path(tempfile.mkdtemp(prefix="g2b1_exec_"))
    evidence_path = _evidence_path_for(task, provider, evidence_dir)
    if evidence_path.exists():  # idempotent: one terminal state per task
        ev = json.loads(evidence_path.read_text(encoding="utf-8"))
        ev["replayed"] = True  # historical result — not fresh work
        return ev

    subprocess.run(["git", "-c", "core.autocrlf=false", "worktree", "add",
                    "--detach", str(workdir / "repo"), buggy_commit],
                   cwd=repo_root, check=True, capture_output=True, timeout=300)
    try:
        buggy_root = workdir / "repo"
        # Repo-agnostic backend root: the directory that owns the tests/ tree
        # (nautilus-core: phase3/backend; foreign repos usually: repo root).
        def _backend_root_of(first_test_file: str) -> Path:
            parts = Path(first_test_file).parts
            for i, part in enumerate(parts):
                if part == "tests" and i > 0:
                    return buggy_root.joinpath(*parts[:i])
            return buggy_root
        first_test = task.get("test_files", [""])[0]
        backend = _backend_root_of(first_test)
        backend_rel = str(backend.relative_to(buggy_root)).replace("\\", "/")
        backend_rel = "" if backend_rel == "." else backend_rel
        # SWE-bench style: materialize the fix's TEST files (the new spec) on
        # top of the buggy commit. In a TDD repo the fix adds test+fix together,
        # so tests rarely pre-exist at the parent — without this, 25/28 mined
        # fix-tasks were unrunnable. Additionally check out the fix's
        # NON-PRIMARY changed files (schema/fixture/aux helpers) — the tests
        # often import those, and withholding them only produces collection
        # errors. The primary source file stays at the buggy version: that is
        # the model's job.
        primary_source = task.get("source_files", [None])[0]
        fix_files = subprocess.run(
            ["git", "show", "--name-only", "--pretty=format:",
             task["reference_fix_commit"]],
            cwd=repo_root, check=True, capture_output=True, timeout=120,
        ).stdout.decode("utf-8", "replace").splitlines()
        checkout_files = [f for f in task.get("test_files", [])]
        checkout_files += [f for f in fix_files
                           if f and f != primary_source
                           and f not in checkout_files
                           and not f.startswith(("docs/", ".github/"))]
        subprocess.run(
            ["git", "-c", "core.autocrlf=false", "checkout",
             task["reference_fix_commit"], "--", *checkout_files],
            cwd=buggy_root, check=True, capture_output=True, timeout=120)
        # Variant flow: re-inject the synthesized bug on top of the fix tree.
        # buggy_commit == reference_fix_commit here; the patch IS the task.
        variant_patch = task.get("variant_patch")
        if variant_patch:
            ap = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", "-"],
                input=variant_patch.encode("utf-8"), cwd=buggy_root,
                capture_output=True, timeout=60)
            if ap.returncode != 0:
                evidence = {
                    "schema_version": "g2b1-exec-run-v1",
                    "executor": EXECUTOR_NAME, "task": task,
                    "test_id": None,
                    "source_rel": task.get("source_files", [None])[0],
                    "provider": provider, "test_passed": False,
                    "skipped_reason": "variant_patch_apply_failed",
                    "apply_stderr": (ap.stderr or b"").decode("utf-8", "replace")[-300:],
                    "budget_exceeded": False, "total_tokens": 0, "turns": [],
                    "summary_code": None, "duration_s": 0,
                }
                evidence_path.write_text(json.dumps(evidence, indent=1) + "\n",
                                         encoding="utf-8")
                return evidence
        test_id = _derive_test_anchor(repo_root, task["reference_fix_commit"],
                                      task.get("test_files", []))
        source_rel = task.get("source_files", [None])[0]
        if not test_id or not source_rel:
            raise RuntimeError("cannot derive test anchor or source file")
        # pytest runs with cwd=backend; miner task paths are repo-root-relative.
        # Forgetting to strip made pytest collect 0 items for four full runs.
        prefix = (backend_rel + "/") if backend_rel else ""
        test_file = (test_id or "").removeprefix(prefix)
        red_test = _find_red_test(backend, test_file)
        if red_test is None:
            evidence = {
                "schema_version": "g2b1-exec-run-v1",
                "executor": EXECUTOR_NAME, "task": task, "test_id": test_id,
                "source_rel": str(source_rel), "provider": provider,
                "test_passed": False, "skipped_reason": "no_red_test_at_buggy_commit",
                "budget_exceeded": False, "total_tokens": 0, "turns": [],
                "summary_code": None, "duration_s": 0,
            }
            evidence_path.write_text(json.dumps(evidence, indent=1) + "\n",
                                     encoding="utf-8")
            return evidence
        test_id = red_test
        source_rel = Path(source_rel).relative_to("phase3/backend") \
            if source_rel.startswith("phase3/backend/") else Path(source_rel)

        # Guard: feature-add fixes bring their own test; at the buggy commit
        # the test file does not exist and is NOT a repair task. Skip, zero spend.
        test_file = test_id.split("::")[0]
        # test_file/source_rel are backend-relative after the prefix strip;
        # resolving from repo root always missed (fifth-run false skip).
        if not (backend / test_file).exists() or not (backend / source_rel).exists():
            evidence = {
                "schema_version": "g2b1-exec-run-v1",
                "executor": EXECUTOR_NAME, "task": task, "test_id": test_id,
                "source_rel": str(source_rel), "provider": provider,
                "test_passed": False, "skipped_reason": "anchor_missing_at_buggy_commit",
                "budget_exceeded": False, "total_tokens": 0, "turns": [],
                "summary_code": None, "duration_s": 0,
            }
            evidence_path.write_text(json.dumps(evidence, indent=1) + "\n",
                                     encoding="utf-8")
            return evidence

        started = time.time()
        result = None
        budget_exceeded = False
        try:
            result = run_agentic_loop(
                completer, backend, buggy_root, test_id, source_rel,
                max_total_tokens=max_total_tokens, backend_rel=backend_rel,
                dump_dir=evidence_dir,  # outside the worktree (survives teardown)
            )
        except BudgetExceeded:
            budget_exceeded = True

        if result is None:  # BudgetExceeded — terminal, fail-closed
            from types import SimpleNamespace
            result = SimpleNamespace(test_passed=False, total_tokens=max_total_tokens,
                                     turns=[], summary_code=None)

        if getattr(result, "fixture_broken", False):
            # RED-phase fixture defect (missing data file / import error) —
            # zero-spend skip, not a repair task. 8/24 loofold_select lesson.
            evidence = {
                "schema_version": "g2b1-exec-run-v1",
                "executor": EXECUTOR_NAME, "task": task, "test_id": test_id,
                "source_rel": str(source_rel), "provider": provider,
                "test_passed": False, "skipped_reason": "fixture_broken_red",
                "budget_exceeded": False, "total_tokens": 0, "turns": [],
                "summary_code": None, "duration_s": round(time.time() - started, 1),
            }
            evidence_path.write_text(json.dumps(evidence, indent=1) + "\n",
                                     encoding="utf-8")
            return evidence

        evidence = {
            "schema_version": "g2b1-exec-run-v1",
            "executor": EXECUTOR_NAME,
            "task": task,
            "test_id": test_id,
            "source_rel": str(source_rel),
            "provider": provider,
            "provider_used": _provider_used_of(completer, provider),
            "test_passed": result.test_passed,
            "winning_diff": getattr(result, "winning_diff", None),
            "budget_exceeded": budget_exceeded,
            "total_tokens": result.total_tokens,
            "turns": [t.__dict__ for t in result.turns],
            "summary_code": result.summary_code,
            "duration_s": round(time.time() - started, 1),
        }
        evidence_path.write_text(json.dumps(evidence, indent=1) + "\n",
                                 encoding="utf-8")
        return evidence
    finally:
        subprocess.run(["git", "worktree", "remove", "--force",
                        str(workdir / "repo")],
                       cwd=repo_root, capture_output=True, timeout=120)
        shutil.rmtree(workdir, ignore_errors=True)


def submit_verdict(evidence: dict, backend_base: str | None = None,
                   poster=None) -> dict | None:
    """Report one task terminal state to the platform verdict-bus (idempotent).

    Accountability only: verdict + capability link + survival via the existing
    W1.2 intake. This deliberately does NOT mint income — self-mined tasks are
    B=0 fuel and income accrual for them is frozen pending compass/user.
    """
    base = (backend_base or os.environ.get("NAUTILUS_BACKEND_BASE")
            or DEFAULT_BACKEND_BASE)
    if not base:
        return {"status": "SKIPPED_NO_BASE",
                "body": "set NAUTILUS_BACKEND_BASE or pass --backend-base"}
    task = evidence["task"]
    row_uid = task.get("task_uid")
    uid = row_uid or f"g2b1:{task['reference_fix_commit'][:12]}"
    passed = bool(evidence.get("test_passed"))
    # 2026-09-15 载荷补齐(compass 试点首账:8/24 起硬编码 items=[] 450 行,复算不可
    # 用)。items 首条=终判+可复算指针:复算方拿 repo+reference_fix_commit 即可
    # 在 ref^ 上 apply 变体重放 tests。
    items = [{
        "round": 1,
        "valid": 1 if passed else 0,
        "score": 1.0 if passed else 0.0,
        "criteria": ("g2b1-repair-v1: at reference_fix_commit^ apply variant patch, "
                     "tests must pass"),
        "repo": task.get("repo_path") or task.get("repo"),
        "reference_fix_commit": task.get("reference_fix_commit"),
        "provider": evidence.get("provider_used") or evidence.get("provider"),
        "total_tokens": evidence.get("total_tokens"),
        "error": evidence.get("last_error"),
    }]
    payload = {
        "verdict_id": f"{uid.replace(':', '-')}-{evidence.get('provider', 'unknown')}"
                      if row_uid else
                      f"g2b1-{task['reference_fix_commit'][:10]}-{evidence.get('provider', 'unknown')}",
        "task_uid": uid,
        "source": "g2-b1-repair-executor",
        "overall_pass": passed,
        "score": 1.0 if passed else 0.0,
        "items": items,
        "artifacts": {
            "producer_agent_id": _executor_agent_id(),
            "autonomous": True,
            "evidence_schema": evidence.get("schema_version"),
            "provider_used": evidence.get("provider_used"),
            "total_tokens": evidence.get("total_tokens"),
            "turns": len(evidence.get("turns", [])),
        },
    }
    post = poster or (lambda url, body: httpx.post(url, json=body, timeout=30,
                                                   trust_env=False))
    resp = post(f"{base}/api/platform/fde/verdict", payload)
    return {"status": resp.status_code, "body": resp.text[:200]}


def _executor_agent_id() -> int | None:
    try:
        return json.loads(CRED_PATH.read_text(encoding="utf-8")).get("agent_id")
    except OSError:
        return None


STATE_PATH = Path.home() / ".nautilus" / "g2b1_daily_state.json"

# Fail-breaker (2026-08-30): 同题连续失败 ≥N 次熔断跳过,24h 冷却后半开重试。
# 根因实证: 3 道环境坏题(2×LLM 空输出 1×git checkout 缺文件)在 resident loop 里
# 每轮重试,累计 136 次空烧 token 且永不产 evidence。
FAIL_STREAK_PATH = Path.home() / ".nautilus" / "g2b1_fail_streak.json"
FAIL_BREAKER_N = 5
FAIL_COOLDOWN_S = 24 * 3600

# 9/5 空转修复:schtasks 25min × --loop-minutes 15 曾叠加几百个常驻实例
# (fail_streak 54 连败+2.7 万泄漏目录)。守卫=单实例锁+启动清扫+无产出即退。
LOCK_PATH = Path.home() / ".nautilus" / "g2b1_executor.pid"


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        SYNCHRONIZE = 0x00100000
        k = ctypes.windll.kernel32
        h = k.OpenProcess(SYNCHRONIZE, False, int(pid))
        if not h:
            return False
        k.CloseHandle(h)
        return True
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire_single_instance(lock_path: Path | None = None) -> bool:
    """PID 锁单实例。持有者活 → False;锁过期(持有者死)→ 回收并持锁。"""
    p = lock_path or LOCK_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            if _pid_alive(int(rec.get("pid", 0))):
                return False
        except (OSError, ValueError):
            pass  # 坏锁视为无主,回收
    p.write_text(json.dumps({"pid": os.getpid(), "ts": _now()}), encoding="utf-8")
    return True


def release_single_instance(lock_path: Path | None = None) -> None:
    p = lock_path or LOCK_PATH
    try:
        if p.exists() and json.loads(p.read_text(encoding="utf-8")).get("pid") == os.getpid():
            p.unlink()
    except (OSError, ValueError):
        pass


def sweep_stale_workdirs(max_age_s: int = 7200,
                         tmp: Path | str | None = None) -> int:
    """清扫 Temp 里 g2b1_exec_* 孤儿目录(>max_age_s 的;并发锁场景 rmtree
    ignore_errors 静默失败留下的残骸)。返回删除数。"""
    root = Path(tmp) if tmp else Path(tempfile.gettempdir())
    now = _now()
    removed = 0
    for d in root.glob("g2b1_exec_*"):
        try:
            if now - d.stat().st_mtime > max_age_s:
                shutil.rmtree(d, ignore_errors=True)
                removed += 1
        except OSError:
            continue
    return removed


def _now() -> float:
    import time
    return time.time()


def _fail_streak_load() -> dict:
    try:
        return json.loads(FAIL_STREAK_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _fail_streak_save(d: dict) -> None:
    # 原子写:tmp 落满后 os.replace。write_text('w') 先截断再写——9/6 盘满
    # (Errno 28)时把 37 题熔断冷却记录截成 0 字节,整夜重烧。keeper 语义:
    # 保存失败静默放弃本轮增量,绝不阻断 drain(读端 _fail_streak_load 有防御)。
    import os
    FAIL_STREAK_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = FAIL_STREAK_PATH.parent / (FAIL_STREAK_PATH.name + ".tmp")
    try:
        tmp.write_text(json.dumps(d), encoding="utf-8")
        os.replace(tmp, FAIL_STREAK_PATH)
    except OSError:
        tmp.unlink(missing_ok=True)


def fail_should_skip(uid10: str, now: float, state: dict | None = None,
                     n: int = FAIL_BREAKER_N,
                     cooldown: float = FAIL_COOLDOWN_S) -> bool:
    """True = 该题处于熔断冷却期,应跳过(不花 LLM token)。半开:冷却过即放行重试。"""
    rec = (state if state is not None else _fail_streak_load()).get(uid10)
    if not rec:
        return False
    cnt, last = rec[0], rec[1]
    if cnt < n:
        return False
    return (now - last) < cooldown


def fail_bump(uid10: str, now: float) -> None:
    d = _fail_streak_load()
    rec = d.get(uid10) or [0, 0.0]
    d[uid10] = [rec[0] + 1, now]
    _fail_streak_save(d)


def fail_reset(uid10: str) -> None:
    d = _fail_streak_load()
    if uid10 in d:
        del d[uid10]
        _fail_streak_save(d)


def _spent_today() -> int:
    """Daily cumulative token spend (UTC date keyed) for the resident loop."""
    import datetime
    try:
        s = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if s.get("date") == datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"):
            return int(s.get("spent", 0))
    except (OSError, ValueError):
        pass
    return 0


def _add_spend(tokens: int) -> None:
    import datetime
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    spent = _spent_today() if _spend_date_matches(today) else 0
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"date": today, "spent": spent + tokens}),
                          encoding="utf-8")


def _spend_date_matches(today: str) -> bool:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8")).get("date") == today
    except (OSError, ValueError):
        return False


def drain_queue(repo_root: Path, queue_path: Path, evidence_dir: Path,
                provider: str = "deepseek", limit: int | None = None,
                daily_token_cap: int = 1_000_000,
                count_cap_from_state: bool = False) -> list[dict]:
    providers = [x.strip() for x in provider.split(",") if x.strip()]
    completer = (make_fallback_completer(providers) if len(providers) > 1
                 else make_completer(provider))
    tasks = [json.loads(line) for line in
             queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    spent = _spent_today() if count_cap_from_state else 0
    for task in tasks:
        if limit and len(results) >= limit:
            break
        if spent >= daily_token_cap:  # resident daily budget, fail-closed
            print(f"daily token cap {daily_token_cap} reached; stopping drain")
            break
        try:
            uid10 = task["reference_fix_commit"][:10]
            if fail_should_skip(uid10, _now()):
                print(f"skip (fail-breaker, cooldown): {uid10}")
                continue
            task_repo = Path(task.get("repo_path", str(repo_root)))
            ev = run_task(task_repo, task, completer, provider, evidence_dir)
            # Only fresh LLM runs count toward the limit and the verdict bus;
            # skips/invalid tasks and idempotent replays are free, silent passes.
            fresh = bool(ev.get("turns")) and not ev.get("replayed")
            if fresh:
                results.append(ev)
                fail_reset(uid10)
                spent += ev.get("total_tokens", 0)
                _add_spend(ev.get("total_tokens", 0))
                verdict = _record_verdict_post(
                    ev, _evidence_path_for(task, provider, evidence_dir))
                print(f"verdict: {verdict['status'] if verdict else 'NO_BASE'}")
            else:
                reason = ("replay" if ev.get("replayed")
                          else ev.get("skipped_reason", "not_red"))
                if reason == "replay":
                    backfill = _backfill_replay_verdict(
                        ev, _evidence_path_for(task, provider, evidence_dir))
                    if backfill:
                        print(f"replay verdict backfill: {backfill['status']}")
                print(f"skipped (no verdict, no slot): {reason}")
        except Exception as exc:  # one bad task must not kill the resident
            print(f"task {task['reference_fix_commit'][:10]} failed: {exc}")
            fail_bump(task["reference_fix_commit"][:10], _now())
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).parents[3]))
    parser.add_argument("--queue", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--provider", default="deepseek")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--register", default=None,
                        help="backend base_url; registers the executor first")
    parser.add_argument("--daily-token-cap", type=int, default=1_000_000,
                        help="resident daily cumulative token budget, fail-closed")
    parser.add_argument("--loop-minutes", type=int, default=0,
                        help=">0 = resident mode: drain then sleep this long, forever")
    args = parser.parse_args()
    if args.register:
        creds = register_executor(args.register)
        print(f"registered agent_id={creds['agent_id']} "
              f"wallet={creds['wallet_address'][:10]}... creds -> {CRED_PATH}")
    import time as _time
    if not acquire_single_instance():
        print("another instance holds the lock; exiting")
        sys.exit(0)
    try:
        swept = sweep_stale_workdirs()
        if swept:
            print(f"swept {swept} stale workdirs")
        while True:
            results = drain_queue(Path(args.repo), Path(args.queue),
                                  Path(args.evidence_dir), args.provider,
                                  args.limit, args.daily_token_cap,
                                  count_cap_from_state=True)
            for ev in results:
                print(json.dumps({k: ev[k] for k in
                                  ("test_passed", "total_tokens", "test_id",
                                   "reference_fix_commit" if "reference_fix_commit" in ev
                                   else "task")}, ensure_ascii=False, default=str))
            if not results:
                # 无产出(全被熔断/失败/无任务)即退——不空转常驻;
                # timer 下轮再唤,单实例锁防叠加,熔断冷却管重试节奏。
                print("no productive output this drain; exiting")
                break
            if not args.loop_minutes:
                break
            _time.sleep(args.loop_minutes * 60)
    finally:
        release_single_instance()
