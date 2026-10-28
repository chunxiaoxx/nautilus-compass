"""Tests for the HumanEval persona-diverse consensus probe (Phase 2).

Phase 1 (bug-detection classification) falsified naive consensus. Phase 2 moves
to code generation with an OBJECTIVE external ground truth (held-out test
execution) and persona-diverse generation, to test whether multi-agent
consensus can beat a single LLM where errors are decorrelated.

Pure logic is tested here with injected sandbox runners (no real code exec, no
real LLM). The integration arm + real sandbox self-check run on cloud Linux.
"""
import pytest

from humaneval_consensus_probe import (
    PERSONAS,
    build_persona_prompt,
    extract_code,
    extract_visible_tests,
    load_humaneval_subset,
    select_by_self_tests,
    score_with_held_out,
)


# --- Task 1: load_humaneval_subset ---

def test_load_subset_returns_n_problems_with_required_fields():
    problems = load_humaneval_subset(5)
    assert len(problems) == 5
    for p in problems:
        assert p["prompt"].strip()          # function signature + docstring
        assert p["test"].strip()            # held-out check(candidate) body
        assert p["entry_point"].strip()     # function name to call
        assert p["task_id"].startswith("HumanEval/")


def test_load_subset_is_deterministic_prefix():
    a = load_humaneval_subset(3)
    b = load_humaneval_subset(3)
    assert [p["task_id"] for p in a] == [p["task_id"] for p in b]


# --- Task 2: build_persona_prompt ---

def _problem():
    return {
        "task_id": "HumanEval/0",
        "prompt": "def has_close(numbers, t):\n    \"\"\"Return True if any two are within t.\"\"\"\n",
        "test": "def check(candidate):\n    assert candidate([1.0, 2.0], 0.5) == False\n",
        "entry_point": "has_close",
    }


def test_persona_prompt_includes_problem_persona_and_output_contract():
    p = _problem()
    prompt = build_persona_prompt(p, "edge-case-first")
    assert "has_close" in prompt                      # the function under work present
    assert "Return True if any two" in prompt         # docstring carried in
    assert PERSONAS["edge-case-first"].split(".")[0][:20] in prompt  # persona framing present
    # output contract: must ask for visible tests AND a final code block
    assert "assert" in prompt.lower()                 # asks for self tests
    assert "```python" in prompt                      # asks for a python code block


def test_persona_prompt_differs_across_personas():
    p = _problem()
    prompts = {name: build_persona_prompt(p, name) for name in
               ("edge-case-first", "spec-literalist", "test-driven")}
    # three orthogonal personas -> three distinct system framings
    assert len(set(prompts.values())) == 3


def test_three_diverse_personas_plus_plain_baseline_exist():
    for name in ("plain", "edge-case-first", "spec-literalist", "test-driven"):
        assert name in PERSONAS and PERSONAS[name].strip()


# --- Task 3: extract_code ---

def test_extract_code_from_python_fence():
    out = "Here is my solution:\n```python\ndef f(x):\n    return x + 1\n```\nDone."
    assert extract_code(out) == "def f(x):\n    return x + 1"


def test_extract_code_from_bare_fence():
    out = "```\ndef g():\n    return 2\n```"
    assert extract_code(out) == "def g():\n    return 2"


def test_extract_code_prefers_block_with_def_over_test_block():
    # Model emits a visible-tests block first, then the implementation block.
    out = (
        "My tests:\n```python\nassert f(1) == 2\nassert f(0) == 1\n```\n"
        "Implementation:\n```python\ndef f(x):\n    return x + 1\n```"
    )
    assert "def f(x):" in extract_code(out)
    assert extract_code(out) == "def f(x):\n    return x + 1"


def test_extract_code_returns_empty_when_no_fence():
    assert extract_code("I cannot solve this problem.") == ""


# --- Task 4: extract_visible_tests ---

def test_extract_visible_tests_from_prose():
    out = "Tests I expect:\nassert f(1) == 2\nassert f(0) == 1\nNow the code."
    assert extract_visible_tests(out) == ["assert f(1) == 2", "assert f(0) == 1"]


def test_extract_visible_tests_inside_code_fence():
    out = "```python\nassert g([]) == 0\nassert g([1]) == 1\n```"
    assert extract_visible_tests(out) == ["assert g([]) == 0", "assert g([1]) == 1"]


def test_extract_visible_tests_none_present():
    assert extract_visible_tests("def f(): return 1") == []


# --- Task 5: select_by_self_tests ---

def test_select_picks_candidate_passing_most_tests():
    candidates = ["A", "BB", "CCC"]
    passes = {"A": 3, "BB": 1, "CCC": 0}
    runner = lambda code, tests: passes[code]
    assert select_by_self_tests(candidates, ["t1", "t2", "t3"], runner) == "A"


def test_select_tie_breaks_to_shortest_code():
    candidates = ["longer_code_x", "short"]
    runner = lambda code, tests: 2  # everyone passes the same number
    assert select_by_self_tests(candidates, ["t1", "t2"], runner) == "short"


def test_select_empty_candidates_returns_empty():
    assert select_by_self_tests([], ["t1"], lambda c, t: 0) == ""


def test_select_no_visible_tests_falls_back_to_first_nonempty():
    # No selection signal -> can't discriminate; return first non-empty candidate.
    candidates = ["", "def f(): pass", "def g(): pass"]
    runner = lambda code, tests: 0
    assert select_by_self_tests(candidates, [], runner) == "def f(): pass"


# --- Task 6: score_with_held_out ---

def test_score_assembles_program_and_returns_runner_verdict():
    p = _problem()
    captured = {}

    def fake_runner(program_src, timeout=6.0):
        captured["src"] = program_src
        return True

    ok = score_with_held_out("def has_close(numbers, t):\n    return False", p,
                             runner=fake_runner)
    assert ok is True
    assert "def has_close" in captured["src"]            # candidate code present
    assert "def check(candidate):" in captured["src"]    # held-out test present
    assert "check(has_close)" in captured["src"]          # entry point invoked


def test_score_empty_code_is_failure_without_running():
    p = _problem()
    called = {"n": 0}

    def fake_runner(program_src, timeout=6.0):
        called["n"] += 1
        return True

    assert score_with_held_out("", p, runner=fake_runner) is False
    assert called["n"] == 0  # don't bother executing empty code


# --- Task 7: run_codegen_arm orchestration (LLM + runners injected) ---

class _FakeLLM:
    def __init__(self):
        self.calls = []

    def chat(self, prompt, system="", max_tokens=4096, temperature=0.3):
        self.calls.append({"temperature": temperature, "prompt": prompt})
        return "```python\ndef f():\n    return 1\n```\nassert f() == 1"


def _arm(problems, mode, llm, heldout_ok):
    from humaneval_consensus_probe import run_codegen_arm
    return run_codegen_arm(
        problems, mode, llm,
        selftest_runner=lambda code, tests: len(tests),
        heldout_runner=lambda src, timeout=6.0: heldout_ok,
    )


def test_arm_single_one_generation_per_problem():
    llm = _FakeLLM()
    res = _arm([_problem(), _problem()], "single", llm, heldout_ok=True)
    assert res["mode"] == "single"
    assert res["n_problems"] == 2
    assert res["passed"] == 2
    assert res["pass_at_1"] == pytest.approx(1.0)
    assert len(llm.calls) == 2  # exactly one sample per problem


def test_arm_persona_diverse_three_generations_per_problem():
    llm = _FakeLLM()
    res = _arm([_problem()], "persona-diverse", llm, heldout_ok=False)
    assert len(llm.calls) == 3                       # one per orthogonal persona
    assert res["passed"] == 0
    assert res["pass_at_1"] == pytest.approx(0.0)


def test_arm_homogeneous_uses_n_samples_at_nonzero_temp():
    llm = _FakeLLM()
    res = _arm([_problem()], "homogeneous", llm, heldout_ok=True)
    assert len(llm.calls) == 3                       # default n=3 samples
    assert all(c["temperature"] > 0 for c in llm.calls)  # sampling, not greedy
    assert res["passed"] == 1


def test_arm_per_item_records_task_id_and_pick():
    llm = _FakeLLM()
    res = _arm([_problem()], "single", llm, heldout_ok=True)
    row = res["per_item"][0]
    assert row["task_id"] == "HumanEval/0"
    assert "def f()" in row["pick"]
    assert row["passed"] is True
