"""S_GBrain module 2 · skill_registry smoke tests."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills_pkg.skill_registry import (
    load_registry, save_registry, rebuild_registry,
    promote, list_by_status, increment_review_count,
    PROMOTE_FROM_TO,
)


def _make_skill(skills_root: Path, name: str, status: str = "codified",
                review_count: int = 0) -> Path:
    skill_dir = skills_root / status / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\nstatus: {status}\nreview_count: {review_count}\n"
        f"handler_path: handler.py\n---\nbody\n",
        encoding="utf-8",
    )
    (skill_dir / "handler.py").write_text(
        "def execute(p, c):\n    return {'ok': True}\n", encoding="utf-8")
    return skill_dir


def test_1_load_empty():
    with tempfile.TemporaryDirectory() as t:
        assert load_registry(Path(t)) == {}
    print("OK 1 empty load")


def test_2_save_load_roundtrip():
    with tempfile.TemporaryDirectory() as t:
        d = {"my-skill": {"name": "my-skill", "status": "codified"}}
        save_registry(Path(t), d)
        assert load_registry(Path(t)) == d
    print("OK 2 roundtrip")


def test_3_rebuild_scans_codified():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        _make_skill(skills_root, "alpha", status="codified")
        _make_skill(skills_root, "beta", status="codified", review_count=3)
        reg = rebuild_registry(skills_root)
        assert "alpha" in reg
        assert "beta" in reg
        assert reg["beta"]["review_count"] == 3
    print("OK 3 rebuild scans codified")


def test_4_rebuild_skips_non_codified_dirs():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        _make_skill(skills_root, "proto", status="prototype")
        _make_skill(skills_root, "good", status="codified")
        reg = rebuild_registry(skills_root)
        assert "good" in reg
        assert "proto" not in reg
    print("OK 4 rebuild skips non-codified")


def test_5_promote_concept_to_prototype():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        _make_skill(skills_root, "c", status="concept")
        result = promote(skills_root, "c", from_status="concept")
        assert result["ok"]
        assert (skills_root / "prototype" / "c").exists()
        assert not (skills_root / "concept" / "c").exists()
    print("OK 5 promote concept → prototype")


def test_6_promote_prototype_to_codified():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        _make_skill(skills_root, "p", status="prototype")
        result = promote(skills_root, "p", from_status="prototype")
        assert result["ok"]
        assert result["to"] == "codified"
        # Frontmatter updated
        text = (skills_root / "codified" / "p" / "SKILL.md").read_text(encoding="utf-8")
        assert "status: codified" in text
        # Registry updated
        reg = load_registry(skills_root)
        assert "p" in reg
    print("OK 6 promote prototype → codified + registry refreshed")


def test_7_promote_invalid_edge():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        result = promote(skills_root, "x", from_status="retired")
        assert not result["ok"]
    print("OK 7 invalid edge rejected")


def test_8_promote_missing_source():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        result = promote(skills_root, "ghost", from_status="prototype")
        assert not result["ok"]
        assert "missing" in result["reason"]
    print("OK 8 missing source rejected")


def test_9_list_by_status():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        _make_skill(skills_root, "a", status="codified")
        _make_skill(skills_root, "b", status="codified")
        _make_skill(skills_root, "c", status="prototype")
        codified = list_by_status(skills_root, "codified")
        assert codified == ["a", "b"]
    print("OK 9 list_by_status")


def test_10_increment_review_count():
    with tempfile.TemporaryDirectory() as t:
        skills_root = Path(t)
        _make_skill(skills_root, "r", status="codified", review_count=0)
        new = increment_review_count(skills_root, "r")
        assert new == 1
        text = (skills_root / "codified" / "r" / "SKILL.md").read_text(encoding="utf-8")
        assert "review_count: 1" in text
    print("OK 10 increment review_count")


def test_11_promote_edges_match_spec():
    assert PROMOTE_FROM_TO["concept"] == "prototype"
    assert PROMOTE_FROM_TO["prototype"] == "codified"
    assert PROMOTE_FROM_TO["codified"] == "retired"
    print("OK 11 edges match SPEC")


if __name__ == "__main__":
    tests = [test_1_load_empty, test_2_save_load_roundtrip, test_3_rebuild_scans_codified,
             test_4_rebuild_skips_non_codified_dirs, test_5_promote_concept_to_prototype,
             test_6_promote_prototype_to_codified, test_7_promote_invalid_edge,
             test_8_promote_missing_source, test_9_list_by_status,
             test_10_increment_review_count, test_11_promote_edges_match_spec]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} skill_registry smoke pass")
