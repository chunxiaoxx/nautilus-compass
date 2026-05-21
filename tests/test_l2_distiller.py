"""S6 module 1 · l2_distiller smoke tests · pure logic · no Ollama call."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.l2_distiller import (
    ollama_available, extractive_fallback, distill_l1_files,
    render_l2_overview, build_l2,
    L2_DIR_NAME, MAX_L1_INPUT_CHARS,
)


def test_1_ollama_availability_safe():
    """ollama_available never raises · returns bool."""
    r = ollama_available(url="http://127.0.0.1:1", timeout=0.5)
    assert isinstance(r, bool)
    print("OK 1 ollama_available safe")


def test_2_extractive_fallback_dedup():
    a = "---\nname: a\n---\n# h\n- item 1\n- item 2\n"
    b = "---\nname: b\n---\n# h\n- item 1\n- item 3\n"  # item 1 dup
    out = extractive_fallback([a, b])
    assert "- item 1" in out
    assert "- item 2" in out
    assert "- item 3" in out
    # Dedup · item 1 only once
    assert out.count("- item 1") == 1
    print("OK 2 extractive dedup")


def test_3_extractive_cap_max_chars():
    big = "\n".join(f"- item {i}" for i in range(1000))
    out = extractive_fallback([big], max_chars=500)
    assert len(out) <= 520  # cap + truncation marker
    print("OK 3 extractive cap")


def test_4_distill_no_ollama_falls_back():
    """If use_ollama=False · fallback path."""
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        f1 = tmp / "l1_a.md"
        f1.write_text("---\nname: a\n---\n- foo\n- bar\n", encoding="utf-8")
        result = distill_l1_files([f1], use_ollama=False)
        assert "- foo" in result
        assert "- bar" in result
    print("OK 4 distill use_ollama=False fallback")


def test_5_distill_empty_input():
    result = distill_l1_files([], use_ollama=False)
    assert "(no L1 input)" in result
    print("OK 5 empty input handled")


def test_6_render_l2_overview_frontmatter():
    out = render_l2_overview("proj-x", [Path("l1_a.md"), Path("l1_b.md")],
                              distilled_body="- summary line 1\n- summary line 2\n")
    assert "name: l2-proj-x" in out
    assert "tier: semantic" in out
    assert "l2_l1_count: 2" in out
    assert "summary line 1" in out
    print("OK 6 render frontmatter")


def test_7_build_l2_no_l1_dir():
    with tempfile.TemporaryDirectory() as t:
        result = build_l2(Path(t), project_id="empty")
        assert result["l1_count"] == 0
        assert "skipped" in result
    print("OK 7 build_l2 graceful no L1 dir")


def test_8_build_l2_with_l1_files():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        l1_dir = tmp / "_l1"
        l1_dir.mkdir()
        (l1_dir / "t-A.md").write_text(
            "---\nname: l1-t-A\n---\n# L1\n- alpha\n- beta\n", encoding="utf-8")
        (l1_dir / "topic_000.md").write_text(
            "---\nname: l1-topic_000\n---\n# L1\n- gamma\n", encoding="utf-8")
        result = build_l2(tmp, project_id="test-proj", use_ollama=False)
        assert result["l1_count"] == 2
        assert result["ollama_used"] is False  # forced off
        out_path = Path(result["l2_path"])
        assert out_path.exists()
        content = out_path.read_text(encoding="utf-8")
        assert "l2-test-proj" in content
        assert "- alpha" in content
    print("OK 8 build_l2 with L1 files")


def test_9_l2_skips_underscore_files():
    """Files starting with _ (like _l2_index) shouldn't be re-processed."""
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        l1_dir = tmp / "_l1"
        l1_dir.mkdir()
        (l1_dir / "valid.md").write_text(
            "---\nname: v\n---\n- x\n", encoding="utf-8")
        (l1_dir / "_internal.md").write_text(
            "---\nname: i\n---\n- ignored\n", encoding="utf-8")
        result = build_l2(tmp, project_id="p", use_ollama=False)
        assert result["l1_count"] == 1
    print("OK 9 skips underscore files")


if __name__ == "__main__":
    tests = [test_1_ollama_availability_safe, test_2_extractive_fallback_dedup,
             test_3_extractive_cap_max_chars, test_4_distill_no_ollama_falls_back,
             test_5_distill_empty_input, test_6_render_l2_overview_frontmatter,
             test_7_build_l2_no_l1_dir, test_8_build_l2_with_l1_files,
             test_9_l2_skips_underscore_files]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} l2_distiller smoke pass")
