"""G2-B1 agentic repair loop: the productized core of the 8/22 three-arm result.

Finding (commit f5355c386): single-completion executors (deepseek / glm-5.2 64k
thinking) misdiagnose the real bug, while an agentic loop with pytest feedback
fixes it same-day. This module is that loop, with:

- injectable completion function (offline tests use fakes; live uses providers)
- injectable test runner (offline tests avoid real pytest)
- cumulative per-task token budget, fail-closed (G2-B1 budget discipline)
- RED precondition: the loop refuses to spend tokens unless the task is RED

Evidence schema: g2-b1-agentic-run-v1 (superset of the single-shot v1 fields).
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Callable

CANDIDATE_SCHEMA_HINT = (
    '{"artifact_version":"g2-b1-candidate-v1","claimed_test_scope":'
    '["public_behavior"],"language":"python","summary_code":"<short_snake_slug>",'
    '"unified_diff":"<unified diff>"}'
)

SYSTEM_PROMPT = (
    "You are a precise bug-fixing engine in an iterative repair loop. Return "
    "ONLY one JSON object, no markdown fences, matching exactly this schema: "
    + CANDIDATE_SCHEMA_HINT
)

# Budget discipline: cumulative across turns, fail-closed, per task.
DEFAULT_MAX_TURNS = 3
DEFAULT_MAX_TOTAL_TOKENS = 200_000


class BudgetExceeded(RuntimeError):
    """Raised when cumulative usage crosses the hard cap. Terminal, no retry."""


@dataclass
class TurnRecord:
    turn: int
    patch_applied: bool
    test_passed: bool
    usage: dict
    feedback_kind: str  # "applied_pass" | "applied_fail" | "apply_error" | "no_json" | "empty_diff" | "test_tamper"
    feedback_excerpt: str = ""


@dataclass
class AgenticResult:
    test_passed: bool
    turns: list[TurnRecord] = field(default_factory=list)
    total_tokens: int = 0
    summary_code: str | None = None
    winning_diff: str | None = None
    budget_exceeded: bool = False
    # RED-phase fixture defect (missing data file / import error in the test's
    # own setup) — not a repair task, zero spend. 8/24: loofold_select burned
    # 147k tokens on turns that could never pass.
    fixture_broken: bool = False


# RED failures that are environment/fixture defects, not the target bug.
# Matches pytest's short summary + traceback ERROR lines.
_FIXTURE_ERROR_PATTERNS = (
    "ModuleNotFoundError",
    "ImportError: cannot import name",
    "ImportError while importing test module",
    "ERROR collecting",
)


def _red_is_fixture_broken(red_output: str, source_rel: Path) -> bool:
    """Classify a RED-phase pytest output as fixture-broken vs a real bug.

    Real bugs CAN legitimately surface as FileNotFoundError — but only when the
    missing path is the primary source file (that file is the model's job).
    A missing data/aux file or an import error means the SWE-bench checkout did
    not bring everything the test needs: unfixable by patching the source.
    """
    for pattern in _FIXTURE_ERROR_PATTERNS:
        if pattern in red_output:
            return True
    if "FileNotFoundError" in red_output:
        # the model's target file missing = real bug; anything else = fixture
        source_name = source_rel.name
        for line in red_output.splitlines():
            if "FileNotFoundError" in line:
                # pytest quotes the missing path with single quotes
                parts = line.split("'")
                missing = parts[1] if len(parts) > 1 else ""
                if source_name and source_name in missing:
                    return False  # primary source missing — a real repair task
        return True
    return False


def _default_run_test(test_id: str, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    # confcutdir = the tests/ root that owns the test file (repo-agnostic).
    test_path = test_id.split("::")[0]
    conf = "tests"
    for i, part in enumerate(Path(test_path).parts):
        if part == "tests" and i > 0:
            conf = str(Path(*Path(test_path).parts[:i]))
            break
    return subprocess.run(
        ["python", "-m", "pytest", test_id, "-q", f"--confcutdir={conf}"],
        cwd=cwd,
        capture_output=True,
        timeout=600,
    )


# Anti-reward-hacking guard (9/7, org-OS doc §4.4): the test is the grading
# contract, not the fix surface. Without this, a diff that deletes the failing
# assertion applies cleanly and "passes" — the loop's only verdict input lies.
_DIFF_FILE_LINE = re.compile(r"^(?:\+\+\+|---) (?:[ab]/)?(.+?)\s*$")


def _diff_touches_tests(diff: str, test_file_rel: Path) -> list[str]:
    """Return the test assets a unified diff touches (empty = clean).

    Guarded: anything under a tests/ directory, any test_*/\*_test.py file,
    and conftest.py (fixtures can manufacture passes too). Applies to both
    repo-root-relative and backend-relative diff paths.
    """
    hits: list[str] = []
    for line in diff.splitlines():
        m = _DIFF_FILE_LINE.match(line)
        if not m or m.group(1) == "/dev/null":
            continue
        p = PurePosixPath(m.group(1))
        is_test = ("tests" in p.parts or "test" in p.parts
                   or p.name.startswith("test_") or p.name.endswith("_test.py")
                   or p.name == "conftest.py")
        if is_test and m.group(1) not in hits:
            hits.append(m.group(1))
    return hits


def _apply_patch(diff: str, backend: Path, repo_root: Path,
                 backend_rel: str = "") -> tuple[bool, str]:
    patch_file = backend / "_g2b1.patch"
    if not diff.endswith("\n"):
        diff += "\n"
    patch_file.write_text(diff, encoding="utf-8")
    # Three resolution modes: model diffs arrive with either backend-relative
    # or repo-root-relative paths. Trying root+--directory on already
    # root-relative paths doubled the prefix (8/22 first run, turns 1-2 dead).
    attempts = [
        (["git", "apply", "--recount", "--ignore-whitespace",
          f"--directory={backend_rel}", "--whitespace=nowarn", str(patch_file)],
         repo_root),
    ] if backend_rel else [
        (["git", "apply", "--recount", "--ignore-whitespace",
          "--whitespace=nowarn", str(patch_file)], backend),
        (["git", "apply", "--recount", "--ignore-whitespace",
          "--whitespace=nowarn", str(patch_file)], repo_root),
    ]
    ok, errors = False, []
    for i, (cmd, cwd) in enumerate(attempts, 1):
        applied = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=60)
        if applied.returncode == 0:
            ok = True
            break
        errors.append(f"[attempt{i} {'backend' if cwd is backend else 'root'}] "
                      + applied.stderr.decode("utf-8", "replace")[:300])
    patch_file.unlink(missing_ok=True)
    return ok, "\n".join(errors)


def _parse_candidate(content: str) -> dict | None:
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return None


def build_prompt(test_id: str, red_tail: str, source_rel: Path,
                 source_text: str, feedback: str | None) -> str:
    parts = [
        "Fix a real bug in this repository.\n\n",
        f"Failing test (currently RED):\n{test_id}\n\n",
        f"--- pytest output ---\n{red_tail}\n--- end pytest output ---\n\n",
        f"Relevant source file (contains the bug):\n--- {source_rel} ---\n{source_text}\n",
    ]
    if feedback:
        parts.append(
            "\nYour previous attempt failed. Feedback on it:\n"
            f"--- feedback ---\n{feedback}\n--- end feedback ---\n\n"
            "Read it carefully and produce a DIFFERENT, corrected patch."
        )
    parts.append(
        "\nProduce the minimal unified diff (a/... b/... headers) that makes the "
        "failing test pass. Output only the JSON object per the system schema; "
        "unified_diff must apply cleanly with git apply."
    )
    return "".join(parts)


def run_agentic_loop(
    complete_fn: Callable[[str], dict],  # prompt -> {content, usage, model, finish_reason}
    backend: Path,
    repo_root: Path,
    test_id: str,
    source_rel: Path,
    run_test_fn: Callable[[str, Path], subprocess.CompletedProcess[bytes]] | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    max_total_tokens: int = DEFAULT_MAX_TOTAL_TOKENS,
    backend_rel: str = "",
    dump_dir: Path | None = None,
) -> AgenticResult:
    """Iterate patch→test→feedback until pass, budget exhaustion, or turn limit.

    dump_dir: where failed raw diffs are kept for offline diagnosis. Must live
    OUTSIDE the buggy worktree — it is destroyed after the task (9/5: dumps
    written into a worktree-local docs/evidence were lost with it).
    """
    run_test = run_test_fn or _default_run_test
    source_text = (backend / source_rel).read_text(encoding="utf-8")
    # SWE-bench tasks check the fix's test file out on top of the buggy tree;
    # the per-turn restore (`git checkout -- .`) would wipe it, so keep a copy.
    test_file_rel = Path(str(test_id).split("::")[0])
    test_file_bytes = (backend / test_file_rel).read_bytes() \
        if (backend / test_file_rel).exists() else None

    # RED precondition — never spend tokens on an already-green task.
    red = run_test(test_id, backend)
    if red.returncode == 0:
        return AgenticResult(test_passed=False)  # task_not_red; caller must drop it
    if b"collected 0 items" in red.stdout:
        # collection failure masquerading as RED (path bug) — invalid, zero spend
        return AgenticResult(test_passed=False)
    red_tail = red.stdout.decode("utf-8", "replace")[-4000:]
    if _red_is_fixture_broken(red_tail, source_rel):
        # fixture defect (missing data file / import error), not a repair task
        return AgenticResult(test_passed=False, fixture_broken=True)

    result = AgenticResult(test_passed=False)
    feedback: str | None = None

    for turn in range(1, max_turns + 1):
        prompt = build_prompt(test_id, red_tail, source_rel, source_text, feedback)
        raw = complete_fn(prompt)
        usage = raw.get("usage", {}) or {}
        result.total_tokens += usage.get("total_tokens", 0) or 0
        if result.total_tokens > max_total_tokens:
            result.budget_exceeded = True
            raise BudgetExceeded(
                f"cumulative {result.total_tokens} > cap {max_total_tokens}"
            )

        candidate = _parse_candidate(raw.get("content", ""))
        if candidate is None or "unified_diff" not in candidate:
            record = TurnRecord(turn, False, False, usage, "no_json",
                                raw.get("content", "")[:500])
            result.turns.append(record)
            feedback = ("Your output was not a valid JSON object with a "
                        "unified_diff field. Return ONLY the JSON object.")
            continue

        # Guard BEFORE apply: a tampered test must never touch the worktree.
        tampered = _diff_touches_tests(candidate["unified_diff"], test_file_rel)
        if tampered:
            msg = ("Your diff modifies TEST files, which are FORBIDDEN — the "
                   "test is the grading contract, not the fix surface: "
                   + ", ".join(tampered)
                   + ". Regenerate a diff that ONLY changes non-test source "
                   "files.")
            result.turns.append(
                TurnRecord(turn, False, False, usage, "test_tamper", msg))
            feedback = msg
            continue

        applied, apply_err = _apply_patch(candidate["unified_diff"], backend,
                                              repo_root, backend_rel)
        if not applied and not candidate["unified_diff"].strip():
            # Say EMPTY explicitly: "No valid patches in input" reads like a
            # tooling fault and the model just tries another angle (9/5 turn2).
            empty_msg = ("Your unified_diff was EMPTY. Regenerate the complete "
                         "unified diff that fixes the failing test; never "
                         "return an empty diff.")
            result.turns.append(
                TurnRecord(turn, False, False, usage, "empty_diff", empty_msg))
            feedback = empty_msg
            continue
        if not applied:
            if dump_dir is not None:  # survives the worktree teardown
                dump_dir.mkdir(parents=True, exist_ok=True)
                (dump_dir / f".g2b1-failed-turn{turn}.patch").write_text(
                    candidate["unified_diff"], encoding="utf-8")
            record = TurnRecord(turn, False, False, usage, "apply_error", apply_err)
            result.turns.append(record)
            feedback = (f"git apply failed:\n{apply_err}\nFix the diff "
                        "headers/hunks. The file is at its ORIGINAL buggy "
                        "state — anchor hunks to that state.")
            continue

        green = run_test(test_id, backend)
        passed = green.returncode == 0
        record = TurnRecord(
            turn, True, passed, usage,
            "applied_pass" if passed else "applied_fail",
            "" if passed else green.stdout.decode("utf-8", "replace")[-4000:],
        )
        result.turns.append(record)
        subprocess.run(["git", "checkout", "--", "."], cwd=backend,
                       capture_output=True, timeout=60)  # restore buggy state
        if test_file_bytes is not None:  # re-materialize the checked-out spec
            tf = backend / test_file_rel
            tf.parent.mkdir(parents=True, exist_ok=True)
            tf.write_bytes(test_file_bytes)
        if passed:
            result.test_passed = True
            result.summary_code = candidate.get("summary_code")
            result.winning_diff = candidate["unified_diff"]  # fuel sampling
            return result
        feedback = (
            "The patch applied but the test STILL FAILS. The worktree has been "
            "restored to the ORIGINAL buggy state — regenerate your diff from "
            "that original state, including ALL changes needed. Latest pytest "
            "output:\n" + green.stdout.decode("utf-8", "replace")[-4000:]
        )

    return result
