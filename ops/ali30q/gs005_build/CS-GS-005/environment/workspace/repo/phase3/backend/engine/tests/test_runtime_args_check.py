"""TDD tests for engine.checks.check_runtime_with_sample_args -- cycle 7.

Closes the gap documented by cycle 6 (test_runtime_does_NOT_catch_main_only_bug)
by auto-detecting CLI entry pattern and invoking with one sample arg.
"""
from pathlib import Path

import pytest

from engine.checks import check_runtime_with_sample_args, run_pipeline


# ---------- detection heuristics ----------

def test_args_argparse_file_invoked_with_help(tmp_path: Path):
    f = tmp_path / "ap.py"
    f.write_text(
        "import argparse\n"
        "if __name__ == '__main__':\n"
        "    parser = argparse.ArgumentParser()\n"
        "    parser.add_argument('task')\n"
        "    parser.parse_args()\n"
    )
    res = check_runtime_with_sample_args(str(f))
    assert res.passed is True
    # --help should be the heuristic for argparse-detected files
    assert "--help" in res.message


def test_args_sys_argv_file_invoked_with_dummy(tmp_path: Path):
    f = tmp_path / "argv.py"
    f.write_text(
        "import sys\n"
        "def main():\n"
        "    if len(sys.argv) < 2:\n"
        "        return 1\n"
        "    return 0\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(main())\n"
    )
    res = check_runtime_with_sample_args(str(f))
    assert res.passed is True


# ---------- canonical cycle 5 bug class catch ----------

def test_args_CATCHES_main_only_bug(tmp_path: Path):
    """The cycle 5 gap: bug gated behind argv that needs args to trigger.
    cycle 6's check_runtime missed this -- cycle 7 catches it."""
    f = tmp_path / "cycle5_repro.py"
    f.write_text(
        "import sys\n"
        "def main():\n"
        "    if len(sys.argv) < 2:\n"
        "        return 1\n"
        "    # Bug: undefined name -- only crashes when args provided\n"
        "    return undefined_xyz_999 + 1\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(main())\n"
    )
    res = check_runtime_with_sample_args(str(f))
    assert res.passed is False  # cycle 7 catches it
    assert "NameError" in res.message or "undefined_xyz_999" in res.message


def test_args_catches_wrapped_exception_via_exit_code(tmp_path: Path):
    """Real cycle 5 pattern: main() body wraps call in try/except and prints
    'Error: ...' before returning 1. No traceback in stderr, but exit code 1.
    Cycle 7 catches this via the exit-code-on-sample-args heuristic."""
    f = tmp_path / "wrapped.py"
    f.write_text(
        "import sys\n"
        "def main():\n"
        "    if len(sys.argv) < 2:\n"
        "        return 1\n"
        "    try:\n"
        "        return undefined_xyz + 1  # NameError\n"
        "    except Exception as e:\n"
        "        print(f'Error: {e}', file=sys.stderr)\n"
        "        return 1\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(main())\n"
    )
    res = check_runtime_with_sample_args(str(f))
    assert res.passed is False
    assert "exit=1" in res.message
    assert "Error" in res.message


def test_args_catches_typeerror_in_main(tmp_path: Path):
    """Closer to the actual cycle 5 bug pattern (missing positional arg to call)."""
    f = tmp_path / "typeerr.py"
    f.write_text(
        "import sys\n"
        "def helper(a, b, c):\n"
        "    return a + b + c\n"
        "def main():\n"
        "    if len(sys.argv) < 2:\n"
        "        return 1\n"
        "    return helper(1, 2)  # TypeError -- missing c\n"
        "if __name__ == '__main__':\n"
        "    sys.exit(main())\n"
    )
    res = check_runtime_with_sample_args(str(f))
    assert res.passed is False
    assert "TypeError" in res.message or "argument" in res.message.lower()


# ---------- defaults / edge cases ----------

def test_args_skips_non_py(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("# hi\n")
    res = check_runtime_with_sample_args(str(f))
    assert res.skipped is True
    assert res.passed is True


def test_args_no_main_guard_invokes_without_args(tmp_path: Path):
    """Library-style file -- no entry point detected -- runs as-is."""
    f = tmp_path / "lib.py"
    f.write_text("x = 1\ny = 2\n")
    res = check_runtime_with_sample_args(str(f))
    assert res.passed is True


def test_args_respects_timeout(tmp_path: Path):
    f = tmp_path / "spin.py"
    f.write_text(
        "import sys\n"
        "import time\n"
        "if __name__ == '__main__':\n"
        "    time.sleep(30)\n"
    )
    res = check_runtime_with_sample_args(str(f), timeout=2)
    assert res.passed is False
    assert "timeout" in res.message.lower()


# ---------- pipeline integration ----------

def test_pipeline_includes_runtime_args_when_enabled(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("x = 1\n")
    result = run_pipeline([str(f)], run_runtime_args=True)
    names = {c["name"] for c in result["checks"]}
    assert "runtime_args" in names


def test_pipeline_excludes_runtime_args_by_default(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("x = 1\n")
    result = run_pipeline([str(f)])
    names = {c["name"] for c in result["checks"]}
    assert "runtime_args" not in names
