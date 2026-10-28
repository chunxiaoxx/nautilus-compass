"""TDD tests for engine.checks · cycle 3 deterministic check pipeline."""
from pathlib import Path

import pytest

from engine.checks import (
    CheckResult,
    check_import,
    check_py_compile,
    check_ruff,
    run_pipeline,
)


# ---------- pythonpath / internal-import ----------

def test_check_import_fails_without_pythonpath_for_internal_import(tmp_path: Path):
    """Staged file with internal import fails check_import when pythonpath=None."""
    # Create a fake internal package in a sibling dir (not on sys.path)
    fake_backend = tmp_path / "fake_backend"
    fake_pkg = fake_backend / "mypackage"
    fake_pkg.mkdir(parents=True)
    (fake_pkg / "__init__.py").write_text("")
    (fake_pkg / "utils.py").write_text("HELLO = 'world'\n")

    # Staged file that imports from that package
    staged = tmp_path / "staged"
    staged.mkdir()
    target = staged / "app.py"
    target.write_text("from mypackage.utils import HELLO\nprint(HELLO)\n")

    # Without pythonpath: import should FAIL (ModuleNotFoundError)
    res = check_import(str(target))
    assert res.passed is False, "Expected import to fail without pythonpath"
    assert "mypackage" in res.message


def test_check_import_passes_with_pythonpath_for_internal_import(tmp_path: Path):
    """Staged file with internal import passes check_import when pythonpath is set."""
    # Same fake package
    fake_backend = tmp_path / "fake_backend"
    fake_pkg = fake_backend / "mypackage"
    fake_pkg.mkdir(parents=True)
    (fake_pkg / "__init__.py").write_text("")
    (fake_pkg / "utils.py").write_text("HELLO = 'world'\n")

    staged = tmp_path / "staged"
    staged.mkdir()
    target = staged / "app.py"
    target.write_text("from mypackage.utils import HELLO\nprint(HELLO)\n")

    # With pythonpath pointing at fake_backend: import should PASS
    res = check_import(str(target), pythonpath=str(fake_backend))
    assert res.passed is True, f"Expected import to pass with pythonpath. Message: {res.message}"


def test_run_pipeline_passes_pythonpath_to_import_check(tmp_path: Path):
    """run_pipeline accepts pythonpath and propagates it to check_import."""
    fake_backend = tmp_path / "fake_backend"
    fake_pkg = fake_backend / "mypackage"
    fake_pkg.mkdir(parents=True)
    (fake_pkg / "__init__.py").write_text("")
    (fake_pkg / "utils.py").write_text("HELLO = 'world'\n")

    staged = tmp_path / "staged"
    staged.mkdir()
    target = staged / "app.py"
    target.write_text("from mypackage.utils import HELLO\nprint(HELLO)\n")

    result = run_pipeline([str(target)], run_ruff=False, pythonpath=str(fake_backend))
    import_checks = [c for c in result["checks"] if c["name"] == "import"]
    assert import_checks, "Expected at least one import check"
    assert import_checks[0]["passed"] is True, (
        f"Expected import check to pass. Message: {import_checks[0]['message']}"
    )


# ---------- py_compile ----------

def test_py_compile_passes_valid_file(tmp_path: Path):
    f = tmp_path / "ok.py"
    f.write_text("x = 1\nprint(x)\n")
    res = check_py_compile(str(f))
    assert res.passed is True
    assert res.skipped is False


def test_py_compile_fails_on_syntax_error(tmp_path: Path):
    f = tmp_path / "broken.py"
    f.write_text("def (\n")
    res = check_py_compile(str(f))
    assert res.passed is False
    assert "broken.py" in res.message or "syntax" in res.message.lower()


def test_py_compile_skips_non_python_file(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("# hi\n")
    res = check_py_compile(str(f))
    assert res.skipped is True
    assert res.passed is True  # skipped = passed-by-default


# ---------- import ----------

def test_import_passes_valid_module(tmp_path: Path):
    f = tmp_path / "mod.py"
    f.write_text("x = 1\n")
    res = check_import(str(f))
    assert res.passed is True


def test_import_fails_when_imports_missing_module(tmp_path: Path):
    f = tmp_path / "bad_import.py"
    f.write_text("import this_module_definitely_does_not_exist_xyz123\n")
    res = check_import(str(f))
    assert res.passed is False
    assert "this_module_definitely_does_not_exist_xyz123" in res.message


def test_import_skips_non_python_file(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("# hi\n")
    res = check_import(str(f))
    assert res.skipped is True


# ---------- ruff ----------

def test_ruff_skips_when_command_missing(tmp_path: Path):
    f = tmp_path / "clean.py"
    f.write_text("x = 1\n")
    res = check_ruff([str(f)], command="nonexistent_ruff_binary_xyz")
    assert res.skipped is True
    assert res.passed is True


def test_ruff_runs_if_available(tmp_path: Path):
    # Clean file · should pass ruff if installed; if ruff missing this is a skip test
    f = tmp_path / "clean.py"
    f.write_text('"""Module."""\n\n\ndef foo() -> int:\n    return 1\n')
    res = check_ruff([str(f)])
    # Either ruff is available (passed=True) or skipped silently
    assert res.passed is True
    if not res.skipped:
        assert "ruff" in res.message.lower() or res.message == ""


# ---------- pipeline ----------

def test_run_pipeline_aggregates_results(tmp_path: Path):
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    result = run_pipeline([str(f)])
    assert "passed" in result
    assert "checks" in result
    assert isinstance(result["checks"], list)
    # Each check has the expected fields
    for c in result["checks"]:
        assert "name" in c
        assert "passed" in c


def test_run_pipeline_passed_true_when_all_pass(tmp_path: Path):
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    result = run_pipeline([str(f)])
    assert result["passed"] is True


def test_run_pipeline_passed_false_when_any_fails(tmp_path: Path):
    bad = tmp_path / "bad.py"
    bad.write_text("def (\n")
    good = tmp_path / "good.py"
    good.write_text("x = 1\n")
    result = run_pipeline([str(bad), str(good)])
    assert result["passed"] is False
    # Should have at least one failed check entry
    assert any(c["passed"] is False for c in result["checks"])


def test_run_pipeline_handles_empty_paths():
    result = run_pipeline([])
    # No files = nothing to check · treat as pass
    assert result["passed"] is True
    assert result["checks"] == []


def test_run_pipeline_can_disable_ruff(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("x = 1\n")
    result = run_pipeline([str(f)], run_ruff=False)
    names = {c["name"] for c in result["checks"]}
    assert "ruff" not in names


# ---------- cycle 12 P1 · check_semantic_preservation ----------

from engine.checks import (  # noqa: E402
    SEMANTIC_PRESERVE_TRIGGER_PHRASES,
    check_semantic_preservation,
    should_apply_semantic_check,
)


def test_should_apply_semantic_check_detects_trigger_phrases():
    assert should_apply_semantic_check("add module docstring · keep ALL other code identical") is True
    assert should_apply_semantic_check("only add a logger import to top of file") is True
    assert should_apply_semantic_check("only change line 56") is True
    assert should_apply_semantic_check("apply this minimal diff to fix the bug") is True
    assert should_apply_semantic_check("please do not refactor anything else") is True


def test_should_apply_semantic_check_skips_open_ended_tasks():
    assert should_apply_semantic_check("rewrite the auth module to use JWT") is False
    assert should_apply_semantic_check("refactor cache.py for clarity") is False
    assert should_apply_semantic_check("") is False
    assert should_apply_semantic_check(None) is False


def test_semantic_check_passes_when_only_docstring_added(tmp_path: Path):
    """Layer 5 BUDDHA-A.1 target: docstring add must preserve all other code."""
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text("import os\n\ndef foo(x):\n    return x + 1\n")
    new.write_text('"""Module docstring."""\nimport os\n\ndef foo(x):\n    return x + 1\n')
    res = check_semantic_preservation(str(orig), str(new))
    assert res.passed is True
    assert res.skipped is False


def test_semantic_check_fails_when_imports_swapped(tmp_path: Path):
    """Layer 5 BUDDHA-A.1 actual regression: Google Translate → Hangul detection swap."""
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text(
        "import googletrans\nimport json\n\n"
        "def translate(text):\n    return googletrans.Translator().translate(text).text\n"
    )
    new.write_text(
        "import re\nimport json5\nimport pathlib\n\n"
        "def detect_hangul(text):\n    return bool(re.search(r'[\\uac00-\\ud7af]', text))\n"
    )
    res = check_semantic_preservation(str(orig), str(new))
    assert res.passed is False
    assert "imports" in res.message
    assert "functions removed" in res.message or "functions added" in res.message


def test_semantic_check_fails_when_function_signature_changed(tmp_path: Path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text("def foo(x, y):\n    return x + y\n")
    new.write_text("def foo(x, y, z=0):\n    return x + y + z\n")
    res = check_semantic_preservation(str(orig), str(new))
    assert res.passed is False
    assert "sig" in res.message


def test_semantic_check_non_strict_tolerates_added_import(tmp_path: Path):
    """Non-strict mode lets imports drift · only function sig changes fail."""
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text("def foo(x):\n    return x\n")
    new.write_text("import logging\n\ndef foo(x):\n    return x\n")
    res = check_semantic_preservation(str(orig), str(new), strict=False)
    assert res.passed is True
    # Diff is still surfaced as message context even when passing in non-strict:
    # (passed=True implies message stays empty unless we explicitly surfaced it;
    # current impl returns empty message on the no-difference path, so on the
    # "imports drift but non-strict tolerates" path the result is also passed
    # with no message · this is fine because the policy is permissive.)


def test_semantic_check_skipped_when_not_py(tmp_path: Path):
    orig = tmp_path / "orig.md"
    new = tmp_path / "new.md"
    orig.write_text("# orig\n")
    new.write_text("# new\n")
    res = check_semantic_preservation(str(orig), str(new))
    assert res.skipped is True
    assert res.passed is True


def test_semantic_check_fails_on_parse_error(tmp_path: Path):
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text("def foo():\n    return 1\n")
    new.write_text("def (\n")  # syntax error
    res = check_semantic_preservation(str(orig), str(new))
    assert res.passed is False
    assert "parse error" in res.message


def test_semantic_trigger_phrases_match_cycle12_prompt():
    """Cross-check: the trigger phrases here mirror DEFAULT_SYSTEM_PROMPT (cycle 12 P0)."""
    from engine.nautilus_engine import DEFAULT_SYSTEM_PROMPT
    for phrase in SEMANTIC_PRESERVE_TRIGGER_PHRASES:
        # Phrases are stored lowercased here · prompt may use mixed case ·
        # compare case-insensitive to ensure both sides reference the same trigger.
        assert phrase in DEFAULT_SYSTEM_PROMPT.lower()


# ---------- cycle 16 · allow_additions + should_allow_additions ----------

from engine.checks import should_allow_additions  # noqa: E402


def test_should_allow_additions_true_for_additive_minimal_change():
    assert should_allow_additions("add a helper function · keep ALL other code identical") is True
    assert should_allow_additions("only add a logger import to top of file") is True
    assert should_allow_additions("introduce a new util · do not refactor") is True
    assert should_allow_additions("append a new entry to the list · minimal diff") is True


def test_should_allow_additions_false_without_additive_verb():
    # Trigger phrase present but no additive verb · stays strict
    assert should_allow_additions("fix the bug in line 56 · keep ALL other code identical") is False
    assert should_allow_additions("rename foo to bar · do not refactor") is False
    assert should_allow_additions("only change line 42") is False


def test_should_allow_additions_false_without_trigger_phrase():
    # Additive verb without minimal-change trigger · semantic check doesn't fire at all
    assert should_allow_additions("add a new auth module") is False
    assert should_allow_additions("rewrite cache.py and introduce a logger") is False
    assert should_allow_additions("") is False
    assert should_allow_additions(None) is False


def test_semantic_check_allow_additions_tolerates_added_import(tmp_path: Path):
    """Cycle 15 false-positive class: spec'd add reported as 'fail' under strict."""
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text("def foo(x):\n    return x\n")
    new.write_text("import logging\n\ndef foo(x):\n    return x\n")
    # Strict mode (default): fails
    strict_res = check_semantic_preservation(str(orig), str(new))
    assert strict_res.passed is False
    # allow_additions mode: passes (import added · no removal · no sig change)
    additive_res = check_semantic_preservation(str(orig), str(new), allow_additions=True)
    assert additive_res.passed is True
    # message still surfaces the added import for caller visibility
    assert "imports added" in additive_res.message


def test_semantic_check_allow_additions_tolerates_added_function(tmp_path: Path):
    """Engine self-bootstrap case (cycle 15): added _helper · everything else identical."""
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text("def existing():\n    return 1\n")
    new.write_text("def existing():\n    return 1\n\n\ndef _helper():\n    return 2\n")
    res = check_semantic_preservation(str(orig), str(new), allow_additions=True)
    assert res.passed is True
    assert "functions added" in res.message


def test_semantic_check_allow_additions_still_fails_on_removed_import(tmp_path: Path):
    """allow_additions only excuses adds · removals still block."""
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text("import os\nimport sys\n\ndef foo():\n    return 1\n")
    new.write_text("import sys\n\ndef foo():\n    return 1\n")  # os removed
    res = check_semantic_preservation(str(orig), str(new), allow_additions=True)
    assert res.passed is False
    assert "imports removed" in res.message


def test_semantic_check_allow_additions_still_fails_on_sig_change(tmp_path: Path):
    """allow_additions does not excuse changed function signatures."""
    orig = tmp_path / "orig.py"
    new = tmp_path / "new.py"
    orig.write_text("def foo(x):\n    return x\n")
    new.write_text("import logging\n\ndef foo(x, y=0):\n    return x + y\n")
    res = check_semantic_preservation(str(orig), str(new), allow_additions=True)
    assert res.passed is False
    assert "sig" in res.message
