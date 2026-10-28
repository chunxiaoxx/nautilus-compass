"""Tests for soul.reviewer — pick_target + review.

TDD: write these first (RED), then implement reviewer.py (GREEN).
"""

import json
import time
from pathlib import Path

import pytest

# Import will fail until reviewer.py exists — that's the RED state.
from soul.reviewer import collect_eligible, pick_target, review


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_soul_dir(tmp_path: Path, names: list[str]) -> Path:
    """Create a fake soul package dir with the given .py filenames."""
    soul_dir = tmp_path / "soul"
    soul_dir.mkdir()
    (soul_dir / "__init__.py").write_text("# init\n")
    tests_dir = soul_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_foo.py").write_text("# test\n")
    for name in names:
        (soul_dir / name).write_text(f"# module {name}\ndef foo(): pass\n")
    return soul_dir


def _fake_gen(response: str):
    """Return a generate_fn that always returns *response*."""
    def generate_fn(prompt: str, system: str = "") -> str:  # noqa: ARG001
        return response
    return generate_fn


# ---------------------------------------------------------------------------
# pick_target tests
# ---------------------------------------------------------------------------

class TestPickTarget:
    def test_skips_init_and_tests(self, tmp_path):
        """__init__.py and files under tests/ must never be returned."""
        soul_dir = _make_soul_dir(tmp_path, ["alpha.py"])
        result = pick_target(soul_dir)
        assert result is not None
        assert result.name != "__init__.py"
        assert "tests" not in result.parts

    def test_returns_py_path(self, tmp_path):
        """Returned path is a .py file inside soul_dir."""
        soul_dir = _make_soul_dir(tmp_path, ["alpha.py"])
        result = pick_target(soul_dir)
        assert result is not None
        assert result.suffix == ".py"
        assert result.parent == soul_dir

    def test_returns_none_when_no_eligible_modules(self, tmp_path):
        """Returns None when only __init__.py exists (no other .py)."""
        soul_dir = _make_soul_dir(tmp_path, [])  # no modules beyond __init__
        result = pick_target(soul_dir)
        assert result is None

    def test_least_recently_reviewed_returned_first(self, tmp_path):
        """Module B (never reviewed) is returned before A (reviewed recently)."""
        soul_dir = _make_soul_dir(tmp_path, ["alpha.py", "beta.py"])
        state_file = tmp_path / "state.json"

        # Mark alpha as recently reviewed
        state_data = {"alpha.py": time.time() - 10}
        state_file.write_text(json.dumps(state_data))

        result = pick_target(soul_dir, state_file=state_file)
        assert result is not None
        assert result.name == "beta.py"

    def test_updates_state_file_after_pick(self, tmp_path):
        """State file records the picked module's timestamp after pick_target."""
        soul_dir = _make_soul_dir(tmp_path, ["gamma.py"])
        state_file = tmp_path / "state.json"

        before = time.time()
        result = pick_target(soul_dir, state_file=state_file)
        after = time.time()

        assert result is not None
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert result.name in state
        assert before <= state[result.name] <= after

    def test_missing_state_file_treated_as_empty(self, tmp_path):
        """A missing state file is treated as empty (no crash)."""
        soul_dir = _make_soul_dir(tmp_path, ["delta.py"])
        state_file = tmp_path / "nonexistent_state.json"

        result = pick_target(soul_dir, state_file=state_file)
        assert result is not None  # should still work

    def test_corrupt_state_file_treated_as_empty(self, tmp_path):
        """A corrupt/invalid JSON state file is treated as empty (no crash)."""
        soul_dir = _make_soul_dir(tmp_path, ["epsilon.py"])
        state_file = tmp_path / "state.json"
        state_file.write_text("NOT VALID JSON }{{{")

        result = pick_target(soul_dir, state_file=state_file)
        assert result is not None  # must not crash

    def test_default_state_file_location(self, tmp_path):
        """Default state file is soul_dir/.soul-review-state.json."""
        soul_dir = _make_soul_dir(tmp_path, ["zeta.py"])
        pick_target(soul_dir)  # no state_file arg
        default_state = soul_dir / ".soul-review-state.json"
        assert default_state.exists()

    def test_rotates_across_two_cycles(self, tmp_path):
        """Two consecutive picks rotate between two modules."""
        soul_dir = _make_soul_dir(tmp_path, ["mod_a.py", "mod_b.py"])
        state_file = tmp_path / "state.json"

        first = pick_target(soul_dir, state_file=state_file)
        second = pick_target(soul_dir, state_file=state_file)

        assert first is not None
        assert second is not None
        assert first.name != second.name


# ---------------------------------------------------------------------------
# collect_eligible + scope-aware pick_target tests (L2 platform-scope)
# ---------------------------------------------------------------------------

def _make_scoped_tree(tmp_path: Path) -> Path:
    """Build a tmp repo tree with soul + engine modules + excluded noise."""
    soul = tmp_path / "phase3" / "soul"
    soul.mkdir(parents=True)
    (soul / "a.py").write_text("# a\n")
    (soul / "__init__.py").write_text("# init\n")
    (soul / "tests").mkdir()
    (soul / "tests" / "test_a.py").write_text("# test\n")
    backend = tmp_path / "phase3" / "backend"
    backend.mkdir(parents=True)
    (backend / "agent_brain.py").write_text("# cognitive — must be excluded\n")
    return tmp_path


class TestCollectEligible:
    def test_filters_init_tests_and_excluded(self, tmp_path):
        repo_root = _make_scoped_tree(tmp_path)
        globs = ("phase3/soul/*.py", "phase3/backend/*.py")
        result = collect_eligible(globs, ("agent_brain",), repo_root)
        names = sorted(p.name for p in result)
        assert names == ["a.py"]

    def test_returns_paths(self, tmp_path):
        repo_root = _make_scoped_tree(tmp_path)
        result = collect_eligible(("phase3/soul/*.py",), (), repo_root)
        assert all(isinstance(p, Path) for p in result)

    def test_dedups(self, tmp_path):
        repo_root = _make_scoped_tree(tmp_path)
        # overlapping globs both match a.py — must appear once
        globs = ("phase3/soul/*.py", "phase3/soul/a*.py")
        result = collect_eligible(globs, (), repo_root)
        rels = [p.relative_to(repo_root).as_posix() for p in result]
        assert rels.count("phase3/soul/a.py") == 1


class TestScopedPickTarget:
    def test_scoped_rotation_two_consecutive_differ(self, tmp_path):
        soul = tmp_path / "phase3" / "soul"
        soul.mkdir(parents=True)
        (soul / "a.py").write_text("# a\n")
        (soul / "b.py").write_text("# b\n")
        state_file = tmp_path / "state.json"
        globs = ("phase3/soul/*.py",)
        first = pick_target(soul, state_file=state_file,
                            scope_globs=globs, repo_root=tmp_path)
        second = pick_target(soul, state_file=state_file,
                             scope_globs=globs, repo_root=tmp_path)
        assert first is not None and second is not None
        assert first.name != second.name

    def test_scoped_key_is_relpath(self, tmp_path):
        soul = tmp_path / "phase3" / "soul"
        soul.mkdir(parents=True)
        (soul / "a.py").write_text("# a\n")
        state_file = tmp_path / "state.json"
        globs = ("phase3/soul/*.py",)
        pick_target(soul, state_file=state_file, scope_globs=globs, repo_root=tmp_path)
        state = json.loads(state_file.read_text())
        assert "phase3/soul/a.py" in state  # keyed by relpath, not bare name


# ---------------------------------------------------------------------------
# review tests
# ---------------------------------------------------------------------------

class TestReview:
    def test_parses_purpose_and_improvement(self, tmp_path):
        """Parses PURPOSE/IMPROVEMENT lines into {target, purpose, description}."""
        soul_dir = _make_soul_dir(tmp_path, ["council.py"])
        module_path = soul_dir / "council.py"

        response = (
            "PURPOSE: Manages multi-persona code proposals.\n"
            "IMPROVEMENT: Add input length validation to prevent oversized prompts."
        )
        result = review(_fake_gen(response), module_path)

        assert result is not None
        assert result["target"] == str(module_path)
        assert "proposal" in result["purpose"].lower() or len(result["purpose"]) > 5
        assert "validation" in result["description"] or len(result["description"]) > 5

    def test_returns_none_on_none_response(self, tmp_path):
        """Returns None when generate_fn responds 'NONE'."""
        soul_dir = _make_soul_dir(tmp_path, ["council.py"])
        module_path = soul_dir / "council.py"

        result = review(_fake_gen("NONE"), module_path)
        assert result is None

    def test_returns_none_on_none_with_whitespace(self, tmp_path):
        """Returns None when 'NONE' has surrounding whitespace/newlines."""
        soul_dir = _make_soul_dir(tmp_path, ["council.py"])
        module_path = soul_dir / "council.py"

        result = review(_fake_gen("  NONE  \n"), module_path)
        assert result is None

    def test_does_not_crash_on_messy_nonNONE_output(self, tmp_path):
        """Returns a dict (not crash) when output is non-NONE but unparseable."""
        soul_dir = _make_soul_dir(tmp_path, ["council.py"])
        module_path = soul_dir / "council.py"

        messy = "This module does stuff. It could be better somehow."
        result = review(_fake_gen(messy), module_path)

        # Must not crash; must return a dict with required keys
        assert result is not None
        assert "target" in result
        assert "purpose" in result
        assert "description" in result

    def test_result_contains_target_as_str(self, tmp_path):
        """result['target'] is a string equal to str(module_path)."""
        soul_dir = _make_soul_dir(tmp_path, ["council.py"])
        module_path = soul_dir / "council.py"

        response = "PURPOSE: Does X.\nIMPROVEMENT: Do Y instead."
        result = review(_fake_gen(response), module_path)

        assert result is not None
        assert isinstance(result["target"], str)
        assert result["target"] == str(module_path)

    def test_purpose_populated_from_purpose_line(self, tmp_path):
        """purpose field matches the PURPOSE: line content."""
        soul_dir = _make_soul_dir(tmp_path, ["council.py"])
        module_path = soul_dir / "council.py"

        response = "PURPOSE: Orchestrates LLM persona voting.\nIMPROVEMENT: Cache repeated calls."
        result = review(_fake_gen(response), module_path)

        assert result is not None
        assert "Orchestrates" in result["purpose"] or "LLM" in result["purpose"]

    def test_description_populated_from_improvement_line(self, tmp_path):
        """description field matches the IMPROVEMENT: line content."""
        soul_dir = _make_soul_dir(tmp_path, ["council.py"])
        module_path = soul_dir / "council.py"

        response = "PURPOSE: Manages proposals.\nIMPROVEMENT: Add retry on transient errors."
        result = review(_fake_gen(response), module_path)

        assert result is not None
        assert "retry" in result["description"] or "transient" in result["description"]
