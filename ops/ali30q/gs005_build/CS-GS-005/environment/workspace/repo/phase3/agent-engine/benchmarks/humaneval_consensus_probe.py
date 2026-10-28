"""HumanEval persona-diverse consensus probe (Phase 2).

Phase 1 falsified naive consensus on binary bug-detection (vote -11.5%, judge 0):
a binary label space gives errors nowhere to decorrelate, and homogeneous
sampling correlates the errors. Phase 2 changes both:

1. Task -> code generation with an OBJECTIVE external ground truth (held-out
   HumanEval test execution), not an LLM judge.
2. Mechanism -> persona-diverse generation (orthogonal failure modes), with the
   agents' own docstring-derived visible tests used to *select* among candidates.

Three arms, pass@1 on a HumanEval subset (scored by held-out tests):
  (1) single                : one plain sample, no selection
  (2) homogeneous best-of-3 : same plain prompt x3, pick by self-tests
  (3) persona-diverse best-of-3 : 3 orthogonal personas, pick by self-tests

  (3)-(1) = total consensus gain (the unlock signal candidate for V5)
  (3)-(2) = persona-diversity net contribution (the orchestration moat test)

Ground truth note: we do NOT use human_eval.check_correctness. It (a) is
Unix-only (reliability_guard imports `resource`/`signal.setitimer`) and (b)
assumes the completion is a body continuation of problem["prompt"], whereas
persona prompts emit a COMPLETE function. We execute the official HumanEval
`test` string (the external ground truth) with a small subprocess runner. The
ground truth stays external; only the executor is ours.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Callable, Dict, List, Optional

# Allow `from llm.client import ...` when run as a script (sys.path[0] = benchmarks/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- Personas (orthogonal failure modes for decorrelated errors) ---

PERSONAS: Dict[str, str] = {
    "plain": "Solve the problem directly and correctly.",
    "edge-case-first": (
        "Enumerate the boundary cases first (empty input, negative values, "
        "zero, single element, out-of-range) and handle each explicitly before "
        "writing the general logic."
    ),
    "spec-literalist": (
        "Re-read the docstring sentence by sentence. Follow the specification "
        "and the return type literally, and verify your code against every "
        "example shown in the docstring."
    ),
    "test-driven": (
        "First write 3-4 test cases derived from the docstring examples, then "
        "implement the function until all of them pass, mentally tracing each."
    ),
}

# The orthogonal personas used for the persona-diverse arm (excludes "plain").
DIVERSE_PERSONAS = ["edge-case-first", "spec-literalist", "test-driven"]


def load_humaneval_subset(n: int) -> List[dict]:
    """Load the first ``n`` HumanEval problems (deterministic prefix).

    Each problem keeps the fields the probe needs: task_id / prompt / test /
    entry_point / canonical_solution. The ``datasets`` cache makes this fast and
    deterministic after the first download.
    """
    from datasets import load_dataset

    ds = load_dataset("openai_humaneval", split="test")
    out = []
    for i in range(min(n, len(ds))):
        r = ds[i]
        out.append({
            "task_id": r["task_id"],
            "prompt": r["prompt"],
            "test": r["test"],
            "entry_point": r["entry_point"],
            "canonical_solution": r["canonical_solution"],
        })
    return out


def build_persona_prompt(problem: dict, persona: str) -> str:
    """Pure: frame a HumanEval problem for one persona, with an output contract.

    The contract asks for (a) docstring-derived visible `assert` tests and (b)
    a single final ```python block with the COMPLETE function. extract_code /
    extract_visible_tests key off that structure.
    """
    instruction = PERSONAS[persona]
    return (
        f"{instruction}\n\n"
        "Complete the following Python function.\n\n"
        f"```python\n{problem['prompt'].rstrip()}\n```\n\n"
        "First, write a few visible test cases as standalone `assert` "
        f"statements calling `{problem['entry_point']}(...)`, derived from the "
        "docstring examples. Then provide the COMPLETE function (including the "
        "signature and any needed imports) as the final answer in a single "
        "```python code block.\n"
    )


_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(llm_output: str) -> str:
    """Extract the implementation code block from free-form LLM output.

    Prefers the last fenced block that defines a function (``def``); falls back
    to the last fenced block; returns "" when no code block is present (scored
    as a failure downstream — no guessing).
    """
    blocks = [b.strip("\n").rstrip() for b in _FENCE_RE.findall(llm_output)]
    if not blocks:
        return ""
    def_blocks = [b for b in blocks if re.search(r"^\s*def\s", b, re.MULTILINE)]
    return (def_blocks or blocks)[-1]


_ASSERT_RE = re.compile(r"^\s*(assert\b.*)$", re.MULTILINE)


def extract_visible_tests(llm_output: str) -> List[str]:
    """Extract the agent's own docstring-derived `assert` statements.

    Single-line asserts only (anywhere in the text, incl. inside code fences).
    These are the only selection signal — held-out tests are never used to
    select (that would be trivial best-of-N, no value).
    """
    return [m.strip() for m in _ASSERT_RE.findall(llm_output)]


def select_by_self_tests(
    candidates: List[str],
    visible_tests: List[str],
    sandbox_runner: Callable[[str, List[str]], int],
) -> str:
    """Pick the candidate that passes the most pooled visible tests.

    ``sandbox_runner(code, tests) -> int`` (number passed) is injected so the
    pure selection logic is testable without executing code. Tie-break: most
    passes, then shortest code, then first (stable). With no tests to
    discriminate, fall back to the first non-empty candidate.
    """
    nonempty = [c for c in candidates if c.strip()]
    if not nonempty:
        return ""
    if not visible_tests:
        return nonempty[0]
    scored = [
        (sandbox_runner(code, visible_tests), -len(code), idx, code)
        for idx, code in enumerate(nonempty)
    ]
    # Max passes; then shortest (-len largest); then lowest idx.
    scored.sort(key=lambda t: (t[0], t[1], -t[2]), reverse=True)
    return scored[0][3]


def run_program(program_src: str, timeout: float = 6.0) -> bool:
    """Execute a self-contained Python program in a subprocess; True iff it
    exits 0 (no assertion error / exception). Cross-platform (no Unix-only
    deps). Runs untrusted LLM code — intended for the cloud sandbox VM."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(program_src)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def make_selftest_runner(timeout: float = 6.0) -> Callable[[str, List[str]], int]:
    """Build a sandbox_runner(code, tests) -> count-passed for selection.

    One subprocess per candidate: each visible assert is wrapped in try/except
    and a pass counter is printed, so a single bad assert can't mask the rest.
    """
    def runner(code: str, tests: List[str]) -> int:
        lines = [code, "", "_passed = 0"]
        for t in tests:
            lines += ["try:", f"    {t}", "    _passed += 1",
                      "except Exception:", "    pass"]
        lines += ["import sys", "sys.stdout.write(str(_passed))"]
        src = "\n".join(lines)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(src)
            path = f.name
        try:
            proc = subprocess.run(
                [sys.executable, path],
                capture_output=True, text=True, timeout=timeout,
            )
            try:
                return int(proc.stdout.strip() or "0")
            except ValueError:
                return 0
        except subprocess.TimeoutExpired:
            return 0
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    return runner


def score_with_held_out(
    pick_code: str,
    problem: dict,
    runner: Optional[Callable[[str, float], bool]] = None,
) -> bool:
    """Score the chosen code against the official held-out HumanEval test.

    Assembles ``pick_code + test + check(entry_point)`` and runs it. Empty code
    is a failure without executing. ``runner(src, timeout) -> bool`` is injected
    in tests; defaults to the real subprocess runner.
    """
    if not pick_code.strip():
        return False
    runner = runner or run_program
    program = (
        f"{pick_code}\n\n"
        f"{problem['test']}\n\n"
        f"check({problem['entry_point']})\n"
    )
    return bool(runner(program))


# --- Integration: three-arm codegen run (real LLM; verified by a real run) ---

GEN_SYSTEM = "You are an expert Python programmer. Write correct, complete code."


def _samples_for_mode(mode: str, n: int, multi_temp: float):
    """(persona, temperature) pairs to generate per problem for each arm."""
    if mode == "single":
        return [("plain", 0.0)]
    if mode == "homogeneous":
        return [("plain", multi_temp)] * n
    if mode == "persona-diverse":
        return [(p, multi_temp) for p in DIVERSE_PERSONAS]
    raise ValueError(f"unknown mode: {mode}")


def _solve_one(problem, mode, llm, selftest_runner, heldout_runner,
               n, multi_temp, max_tokens):
    """Generate -> extract -> select-by-self-tests -> score one problem."""
    plan = _samples_for_mode(mode, n, multi_temp)
    outputs = [
        llm.chat(
            prompt=build_persona_prompt(problem, persona),
            system=GEN_SYSTEM, temperature=temp, max_tokens=max_tokens,
        )
        for persona, temp in plan
    ]
    codes = [extract_code(o) for o in outputs]
    if mode == "single":
        pick = codes[0]
        n_visible = 0
    else:
        visible = []
        for o in outputs:
            visible.extend(extract_visible_tests(o))
        n_visible = len(visible)
        pick = select_by_self_tests(codes, visible, selftest_runner)
    passed = score_with_held_out(pick, problem, runner=heldout_runner)
    return {
        "task_id": problem["task_id"],
        "entry_point": problem["entry_point"],
        "n_samples": len(plan),
        "n_visible_tests": n_visible,
        "pick": pick,
        "passed": passed,
    }


def run_codegen_arm(
    problems: List[dict],
    mode: str,
    llm,
    selftest_runner: Callable[[str, List[str]], int],
    heldout_runner: Optional[Callable[[str, float], bool]] = None,
    n: int = 3,
    multi_temp: float = 0.7,
    max_tokens: int = 16000,
    max_workers: int = 4,
) -> Dict:
    """Run one arm (single / homogeneous / persona-diverse) over the subset.

    LLM and runners are injected (so orchestration is unit-tested without real
    calls). Problems run concurrently (LLM calls are I/O-bound). Returns
    pass@1 + per-item breakdown for the honesty audit.
    """
    from concurrent.futures import ThreadPoolExecutor

    def work(p):
        return _solve_one(p, mode, llm, selftest_runner, heldout_runner,
                          n, multi_temp, max_tokens)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        per_item = list(ex.map(work, problems))

    total = len(problems)
    passed = sum(1 for r in per_item if r["passed"])
    return {
        "mode": mode,
        "n_problems": total,
        "passed": passed,
        "pass_at_1": passed / total if total else 0.0,
        "per_item": per_item,
    }


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    n_problems = int(argv[0]) if argv else 30
    max_workers = int(argv[1]) if len(argv) > 1 else 4

    from llm.client import get_llm_client
    llm = get_llm_client()
    problems = load_humaneval_subset(n_problems)
    selftest_runner = make_selftest_runner()
    heldout_runner = run_program

    print(f"HumanEval persona-diverse consensus probe | N={len(problems)} | "
          f"workers={max_workers} | model={getattr(llm, 'model', '?')}")

    results = {}
    for mode in ("single", "homogeneous", "persona-diverse"):
        print(f"\n>>> arm: {mode} ...")
        res = run_codegen_arm(
            problems, mode, llm,
            selftest_runner=selftest_runner, heldout_runner=heldout_runner,
            max_workers=max_workers,
        )
        results[mode] = res
        print(f"    pass@1 = {res['pass_at_1']:.1%} "
              f"({res['passed']}/{res['n_problems']})")

    s = results["single"]["pass_at_1"]
    h = results["homogeneous"]["pass_at_1"]
    d = results["persona-diverse"]["pass_at_1"]
    summary = {
        "n_problems": len(problems),
        "model": getattr(llm, "model", None),
        "single_pass_at_1": s,
        "homogeneous_pass_at_1": h,
        "persona_diverse_pass_at_1": d,
        "delta_consensus_total": d - s,      # (3)-(1)
        "delta_persona_net": d - h,          # (3)-(2)
        "results": results,
    }
    out_path = os.path.join(os.path.dirname(__file__), "humaneval_consensus_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 64)
    print(f"  (1) single             : {s:.1%}")
    print(f"  (2) homogeneous best-3 : {h:.1%}")
    print(f"  (3) persona-diverse b-3: {d:.1%}")
    print(f"  (3)-(1) consensus total: {d - s:+.1%}")
    print(f"  (3)-(2) persona net    : {d - h:+.1%}")
    print("=" * 64)
    print(f"\nWritten to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
