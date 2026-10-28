"""G2-B1 L2 纵向记忆实验(9/8):相似题 winning_diff 注入能否提升首轮修复。

设计正本(预注册):docs/research/2026-09-07-coding域RSI深挖-从PathB到纵向记忆.md §5
- 三臂:A=无注入(现状)/B=相似题 diff 注入/C=随机 placebo(排"任何 few-shot 都涨")
- 题为自身对照(配对);主门=FAIL 子集 B 首轮通过>0 且>C;次门=sign test
- 单轮判据(patch runner.DEFAULT_MAX_TURNS=1):首轮通过率+单位 token
- 同模型同臂:chunxiao_k3 单臂无 fallback;plan 阶段冻结 B/C 检索结果(防 p-hacking)
- 幂等:run_task evidence 文件已存在即 replay(断点续跑免费)

用法:
  python tools/g2_b1_l2_memory_experiment.py --plan     # 生成并冻结 holdout+B/C
  python tools/g2_b1_l2_memory_experiment.py --run      # 三臂跑,落 experiments/
  python tools/g2_b1_l2_memory_experiment.py --report   # 汇总读数+sign test
"""

from __future__ import annotations

import json
import math
import random
import subprocess  # noqa: F401  (re-exported context parity with executor)
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import g2_b1_agentic_runner as runner  # noqa: E402
import g2_b1_executor_agent as ex  # noqa: E402

BACKEND = TOOLS.parent
EVIDENCE_DIR = BACKEND / "docs/evidence"
EXP_DIR = BACKEND / "docs/evidence/g2b1_l2_20260908"
HOLDOUT_FILE = EXP_DIR / "l2_holdout_20260908.jsonl"
PROVIDER = "chunxiao_k3"
N_PASS, N_FAIL = 6, 6
PLACEBO_SEED = 42


# ---------- pure functions (unit-tested) ----------

def score_memory(task: dict, mem: dict) -> int:
    """Retrieval score: same file > same top dir > same repo (v0 rule-based)."""
    t_src = (task.get("source_files") or [""])[0]
    m_src = mem.get("source_rel") or ""
    if not t_src or not m_src:
        return 0
    tp, mp = t_src.replace("\\", "/"), m_src.replace("\\", "/")
    s = 0
    if Path(tp).name == Path(mp).name:
        s += 3
    elif Path(tp).parts[0] == Path(mp).parts[0]:
        s += 2
    if task.get("repo_path") == mem.get("repo_path"):
        s += 1
    return s


def pick_memory(task: dict, pool: list[dict]) -> dict | None:
    """Top-scored PASS memory; the task itself (same ref commit) is excluded."""
    best, best_score = None, -1
    for mem in pool:
        if mem.get("reference_fix_commit") == task["reference_fix_commit"]:
            continue  # self-leakage guard (doc §5 防泄漏)
        s = score_memory(task, mem)
        if s > best_score or (s == best_score and best is not None
                              and len(mem.get("winning_diff") or "")
                              < len(best.get("winning_diff") or "")):
            best, best_score = mem, s
    return best


def pick_placebo(task: dict, pool: list[dict], seed: int) -> dict | None:
    """Random memory from a DIFFERENT repo AND different file name."""
    t_src = (task.get("source_files") or [""])[0]
    cands = [m for m in pool
             if m.get("repo_path") != task.get("repo_path")
             and Path((m.get("source_rel") or "x/y.py").replace("\\", "/")).name
             != Path((t_src or "a/b.py").replace("\\", "/")).name]
    return random.Random(seed).choice(cands) if cands else None


def build_injection(mem: dict) -> str:
    subject = mem.get("subject") or mem.get("task", {}).get("subject", "")
    return ("REFERENCE FIX FROM A SIMILAR PAST BUG (advisory only — the repo "
            "below is at a different state; do NOT apply this diff verbatim, "
            "extract the fix pattern):\n"
            f"--- past bug subject: {subject}\n"
            f"--- past fix diff:\n{mem['winning_diff']}\n"
            "--- end reference ---\n\n")


def sign_test_p(diffs: list[int]) -> float:
    """Two-sided sign test on paired diffs (zeros ignored)."""
    vals = [d for d in diffs if d != 0]
    n = len(vals)
    if n == 0:
        return 1.0
    s = sum(1 for d in vals if d > 0)
    tail = sum(math.comb(n, k) for k in range(max(s, n - s), n + 1))
    return min(1.0, 2 * tail / 2 ** n)


# ---------- plan: freeze holdout + B/C picks ----------

def load_pool() -> list[dict]:
    pool = []
    for f in EVIDENCE_DIR.glob("g2b1-exec-*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("test_passed") and d.get("winning_diff") and d.get("task"):
            t = d["task"]
            pool.append({
                "source_rel": d.get("source_rel"),
                "repo_path": t.get("repo_path"),
                "reference_fix_commit": t["reference_fix_commit"],
                "winning_diff": d["winning_diff"],
                "task": t, "test_id": d.get("test_id"),
                "past_test_passed": True,
            })
    return pool


def load_terminal() -> list[dict]:
    """All consumed tasks with their historical outcome (pass/fail only)."""
    out = {}
    for f in EVIDENCE_DIR.glob("g2b1-exec-*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        t = d.get("task")
        if not t or d.get("skipped_reason"):
            continue
        if not d.get("turns"):
            continue  # no real LLM turns (skip variants)
        key = t["reference_fix_commit"]
        prev = out.get(key)
        passed = bool(d.get("test_passed"))
        if prev is None or (passed and not prev["_passed"]):
            out[key] = {**t, "hist_test_id": d.get("test_id"),
                        "hist_passed": passed, "_passed": passed}
    return list(out.values())


def plan() -> int:
    pool = load_pool()
    terminals = load_terminal()
    rng = random.Random(PLACEBO_SEED)
    picks, repos_seen = [], set()
    passes = [t for t in terminals if t["hist_passed"]]
    fails = [t for t in terminals if not t["hist_passed"]]
    # spread repos first, then fill
    def _spread(cands, n):
        chosen = []
        for prefer_new in (True, False):
            for c in cands:
                if len(chosen) >= n:
                    break
                if c in chosen:
                    continue
                rp = c.get("repo_path")
                if prefer_new and rp in repos_seen:
                    continue
                chosen.append(c)
                repos_seen.add(rp)
        return chosen[:n]

    picks += _spread(passes, N_PASS)
    picks += _spread(fails, N_FAIL)
    rows = []
    for t in picks:
        mem_b = pick_memory(t, pool)
        mem_c = pick_placebo(t, pool, seed=rng.randrange(1 << 30))
        rows.append({"task": t, "arm_b": _slim(mem_b), "arm_c": _slim(mem_c)})
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    HOLDOUT_FILE.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8")
    print(f"holdout frozen: {len(rows)} tasks -> {HOLDOUT_FILE}")
    for i, r in enumerate(rows, 1):
        print(f"  {i:2d}. {'PASS' if r['task']['hist_passed'] else 'FAIL'} "
              f"{r['task'].get('repo_path', '?').split('/')[-1]} "
              f"{r['task'].get('source_files', ['?'])[0]} "
              f"B={'same-repo' if r['arm_b'] else 'NONE'} C={'ok' if r['arm_c'] else 'NONE'}")
    return 0


def _slim(mem: dict | None) -> dict | None:
    if mem is None:
        return None
    return {"source_rel": mem["source_rel"], "repo_path": mem["repo_path"],
            "reference_fix_commit": mem["reference_fix_commit"],
            "winning_diff": mem["winning_diff"],
            "subject": mem["task"].get("subject", "")}


# ---------- run: three arms via run_task (idempotent, evidence in EXP_DIR) ----------

REPO_ALIASES = {  # legacy queue rows carry bare repo names (path drift 9/7)
    "nautilus-core": "C:/Users/chunx/Projects/nautilus-core",
    "nautilus-compass": "C:/Users/chunx/Projects/nautilus-compass",
    "nautilus-fde-phase3": "C:/Users/chunx/Projects/nautilus-fde-phase3",
    "nautilus-v5": "C:/Users/chunx/nautilus-v5",
    "nautilusflywheel": "C:/Users/chunx/Projects/nautilusflywheel",
}


def _resolve_repo(rp: str | None) -> str | None:
    if not rp:
        return None
    p = Path(rp.replace("\\", "/"))
    if not p.is_absolute():
        rp = REPO_ALIASES.get(rp, rp)
    elif not Path(rp).exists():
        # legacy queue rows wrote stale paths (e.g. Projects\nautilus-v5);
        # fall back to the known-live location by repo name
        rp = REPO_ALIASES.get(p.name, rp)
    return rp


def _infer_repo(task: dict) -> str | None:
    """repo_path alias resolution, then source-path heuristic for None."""
    rp = _resolve_repo(task.get("repo_path"))
    if rp and Path(rp).exists():
        return rp
    src = (task.get("source_files") or [""])[0].replace("\\", "/")
    for prefix, name in (("phase3/backend/", "nautilus-core"),
                         ("fde_capsule/", "nautilus-v5"),
                         ("nautilus_v5/", "nautilus-v5"),
                         ("src/nautilus_fde_phase3/", "nautilus-fde-phase3"),
                         ("mcp_durable/", "nautilus-compass")):
        if src.startswith(prefix):
            return REPO_ALIASES[name]
    return None


def _arm_injector(mem: dict | None):
    orig = runner.build_prompt

    def wrapped(test_id, red_tail, source_rel, source_text, feedback):
        base = orig(test_id, red_tail, source_rel, source_text, feedback)
        return (build_injection(mem) + base) if mem else base

    return wrapped, orig


def run() -> int:
    import time
    rows = [json.loads(l) for l in
            HOLDOUT_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    completer = ex.make_completer(PROVIDER)
    runner.DEFAULT_MAX_TURNS = 1  # first-turn criterion (doc §5)
    for i, row in enumerate(rows, 1):
        task = row["task"]
        repo = _infer_repo(task)
        if repo is None:
            print(f"[{i}/{len(rows)}] SKIP no resolvable repo "
                  f"({task.get('source_files', ['?'])[0]})", flush=True)
            continue
        repo = Path(repo)
        for arm, mem in (("A", None), ("B", row.get("arm_b")),
                         ("C", row.get("arm_c"))):
            wrapped, orig = _arm_injector(mem)
            runner.build_prompt = wrapped if mem else orig
            tag = f"l2{arm}-{PROVIDER}"
            started = time.time()
            try:
                ev = ex.run_task(repo, task, completer, tag, EXP_DIR)
            except Exception as exc:
                print(f"[{i}/{len(rows)}] {arm} ERROR {exc}", flush=True)
                continue
            first = (ev.get("turns") or [{}])[0]
            print(f"[{i}/{len(rows)}] {arm} passed={ev.get('test_passed')} "
                  f"first_turn={first.get('test_passed')} "
                  f"tokens={ev.get('total_tokens')} "
                  f"({time.time() - started:.0f}s)", flush=True)
    runner.build_prompt = _arm_injector(None)[1] if False else runner.build_prompt
    return 0


# ---------- report ----------

def report() -> int:
    rows = [json.loads(l) for l in
            HOLDOUT_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    table = {}
    for arm in "ABC":
        table[arm] = {"first_pass": 0, "tokens": [], "fail_first_pass": 0, "n": 0}
    paired_pass, paired_tok, fail_lifts = [], [], []
    for row in rows:
        hist_fail = not row["task"].get("hist_passed")
        per = {}
        for arm in "ABC":
            p = EXP_DIR / f"g2b1-exec-{_hash10(row['task'])}-l2{arm}-{PROVIDER}.json"
            if not p.exists():
                per[arm] = None
                continue
            d = json.loads(p.read_text(encoding="utf-8"))
            turns = d.get("turns") or [{}]
            fp = bool(turns[0].get("test_passed"))
            per[arm] = {"fp": fp, "tok": d.get("total_tokens", 0)}
            t = table[arm]
            t["n"] += 1
            t["tokens"].append(d.get("total_tokens", 0))
            if fp:
                t["first_pass"] += 1
                if hist_fail:
                    t["fail_first_pass"] += 1
        if all(per.get(a) for a in "ABC"):
            paired_pass.append(1 if per["B"]["fp"] else 0
                               if not per["A"]["fp"] else -1)
            paired_tok.append(per["A"]["tok"] - per["B"]["tok"])
            if hist_fail and per["B"]["fp"]:
                fail_lifts.append(row["task"].get("source_files", ["?"])[0])
    print("=== L2 三臂读数(首轮判据)===")
    for arm in "ABC":
        t = table[arm]
        toks = t["tokens"] or [0]
        print(f"  {arm}: n={t['n']} first_pass={t['first_pass']} "
              f"(fail-subset {t['fail_first_pass']}) "
              f"mean_tokens={sum(toks) / len(toks):.0f}")
    print(f"paired pass sign test B vs A: p={sign_test_p(paired_pass):.4f}")
    print(f"paired token delta (A-B) mean="
          f"{sum(paired_tok) / len(paired_tok) if paired_tok else 0:.0f}")
    print(f"FAIL-subset lifts by B: {fail_lifts or 'none'}")
    print("主门(预注册):FAIL 子集 B first_pass>0 且 >C;次门:sign test p<0.05")
    return 0


def _hash10(task: dict) -> str:
    # executor's evidence filename = reference_fix_commit short hash
    # (memory g2b1-agentic-feedback-fix: NOT a task id, NOT a synthetic hash)
    return task["reference_fix_commit"][:10]


if __name__ == "__main__":
    if "--plan" in sys.argv:
        raise SystemExit(plan())
    if "--run" in sys.argv:
        raise SystemExit(run())
    if "--report" in sys.argv:
        raise SystemExit(report())
    print(__doc__)
    raise SystemExit(2)
