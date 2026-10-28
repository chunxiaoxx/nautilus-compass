"""Multi-file proposal import checks (2026-09-10, soul activation day).

A two-file proposal (utils/x.py + tests/test_x.py) must pass the import
check: the test imports its sibling module, which lives in the SAME staging
root. The old single-value pythonpath only exposed the real backend tree, so
cross-directory imports between staged files always failed with
ModuleNotFoundError (obscured on the proposal queue as empty-looking
"check pipeline failed" verdicts).
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.checks import check_import


def _make_two_file_staging(tmp_path: Path) -> Path:
    (tmp_path / "utils").mkdir()
    (tmp_path / "utils" / "__init__.py").write_text("")
    (tmp_path / "utils" / "x.py").write_text("VALUE = 41\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text(
        "from utils.x import VALUE\nassert VALUE == 41\n"
    )
    return tmp_path


def test_staged_test_file_can_import_staged_module(tmp_path):
    root = _make_two_file_staging(tmp_path)
    pp = os.pathsep.join([str(root), str(Path(__file__).parent.parent)])
    r = check_import(str(root / "tests" / "test_x.py"), pythonpath=pp)
    assert r.passed, r.message


def test_pythonpath_cleanup_restores_all_inserted_paths(tmp_path):
    root = _make_two_file_staging(tmp_path)
    pp = os.pathsep.join([str(root), str(Path(__file__).parent.parent)])
    before = list(sys.path)
    check_import(str(root / "tests" / "test_x.py"), pythonpath=pp)
    assert sys.path == before


def test_single_file_still_passes(tmp_path):
    f = tmp_path / "solo.py"
    f.write_text("X = 1\n")
    r = check_import(str(f), pythonpath=None)
    assert r.passed, r.message
