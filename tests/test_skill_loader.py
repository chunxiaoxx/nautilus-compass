"""S_GBrain module 1 · skill_loader smoke tests."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills_pkg.skill_loader import (
    parse_skill_md, is_codified_path, load_handler,
    SkillSchemaError, VALID_STATUSES,
)


def _make_skill(skills_root: Path, name: str, status: str = "codified",
                handler_body: str = "def execute(payload, context):\n    return {'ok': True}\n",
                under: str = "codified") -> Path:
    skill_dir = skills_root / under / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\nstatus: {status}\nhandler_path: handler.py\n---\nbody\n",
        encoding="utf-8",
    )
    (skill_dir / "handler.py").write_text(handler_body, encoding="utf-8")
    return skill_dir


def test_1_parse_valid():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        d = _make_skill(skills_root, "test")
        front = parse_skill_md(d)
        assert front["name"] == "test"
        assert front["status"] == "codified"
    print("OK 1 parse valid SKILL.md")


def test_2_missing_skill_md_raises():
    with tempfile.TemporaryDirectory() as t:
        try:
            parse_skill_md(Path(t))
        except SkillSchemaError:
            print("OK 2 missing SKILL.md raises")
            return
        raise AssertionError("should have raised")


def test_3_invalid_status_raises():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        d = _make_skill(skills_root, "bad", status="ALIEN")
        try:
            parse_skill_md(d)
        except SkillSchemaError:
            print("OK 3 invalid status raises")
            return
        raise AssertionError("should have raised")


def test_4_is_codified_path_true():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        d = skills_root / "codified" / "x"
        d.mkdir(parents=True)
        assert is_codified_path(d, skills_root)
    print("OK 4 codified path whitelist OK")


def test_5_is_codified_path_false_for_prototype():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        d = skills_root / "prototypes" / "x"
        d.mkdir(parents=True)
        assert not is_codified_path(d, skills_root)
    print("OK 5 prototype path NOT whitelisted")


def test_6_load_handler_success():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        d = _make_skill(skills_root, "ok-skill")
        fn = load_handler(d, skills_root=skills_root)
        assert fn is not None
        result = fn({"key": "val"}, {})
        assert result == {"ok": True}
    print("OK 6 load_handler success")


def test_7_load_handler_status_not_codified():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        d = _make_skill(skills_root, "proto", status="prototype",
                        under="codified")  # under codified but status mismatch
        fn = load_handler(d, skills_root=skills_root)
        assert fn is None
    print("OK 7 non-codified status returns None")


def test_8_load_handler_outside_codified():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        d = _make_skill(skills_root, "rogue", under="prototypes")
        fn = load_handler(d, skills_root=skills_root)
        assert fn is None
    print("OK 8 outside codified rejected by whitelist")


def test_9_load_handler_no_execute_fn():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        d = _make_skill(skills_root, "no-exec",
                         handler_body="def something_else():\n    pass\n")
        fn = load_handler(d, skills_root=skills_root)
        assert fn is None
    print("OK 9 missing execute fn returns None")


def test_10_valid_statuses_match_spec():
    assert set(VALID_STATUSES) == {"concept", "prototype", "codified", "retired"}
    print("OK 10 statuses match SPEC")


if __name__ == "__main__":
    tests = [test_1_parse_valid, test_2_missing_skill_md_raises,
             test_3_invalid_status_raises, test_4_is_codified_path_true,
             test_5_is_codified_path_false_for_prototype, test_6_load_handler_success,
             test_7_load_handler_status_not_codified, test_8_load_handler_outside_codified,
             test_9_load_handler_no_execute_fn, test_10_valid_statuses_match_spec]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} skill_loader smoke pass")
