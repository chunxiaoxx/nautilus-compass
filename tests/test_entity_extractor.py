"""GBrain auto entity extraction smoke tests."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.entity_extractor import (
    extract_entities, extract_session_refs, build_session_links,
    extract_typed_links, rewrite_inline_links, scan_session_file,
    VALID_NAMESPACES,
)


def test_1_extract_basic():
    text = "see [[people/alice]] and [[companies/acme-corp]]"
    entities = extract_entities(text)
    assert len(entities) == 2
    assert entities[0][:2] == ("people", "alice")
    assert entities[1][:2] == ("companies", "acme-corp")
    print("OK 1 extract basic")


def test_2_session_refs_filter():
    text = "[[sessions/session_a]] cites [[people/bob]] and [[sessions/session_b]]"
    refs = extract_session_refs(text)
    assert refs == ["session_a", "session_b"]
    print("OK 2 session refs filter")


def test_3_invalid_namespace_ignored():
    text = "[[invalid_ns/x]] and [[wiki/legit]]"
    entities = extract_entities(text)
    assert len(entities) == 1
    assert entities[0][0] == "wiki"
    print("OK 3 invalid namespace ignored")


def test_4_dedup():
    text = "[[sessions/x]] foo [[sessions/x]] bar [[sessions/x]]"
    refs = extract_session_refs(text)
    assert refs == ["x"]
    print("OK 4 dedup session refs")


def test_5_build_session_links_merge_existing():
    text = "body mentions [[sessions/auto_a]] and [[sessions/auto_b]]"
    existing = ["explicit_a.md"]
    merged = build_session_links(text, existing)
    assert merged[0] == "explicit_a.md"
    assert "auto_a.md" in merged
    assert "auto_b.md" in merged
    print("OK 5 merge explicit + auto-extracted")


def test_6_build_session_links_md_suffix_normalize():
    text = "[[sessions/no_suffix]]"
    merged = build_session_links(text)
    assert merged == ["no_suffix.md"]
    print("OK 6 .md suffix auto-normalize")


def test_7_typed_links_grouping():
    text = "[[people/a]] [[people/b]] [[companies/c]] [[wiki/d]]"
    grouped = extract_typed_links(text)
    assert grouped["people"] == ["a", "b"]
    assert grouped["companies"] == ["c"]
    assert grouped["wiki"] == ["d"]
    assert "sessions" not in grouped  # empty namespace omitted
    print("OK 7 typed links grouping")


def test_8_rewrite_inline_links():
    text = "talk to [[people/alice]]"
    resolved = rewrite_inline_links(text, target_path_resolver=lambda ns, n: f"/{ns}/{n}.md")
    assert resolved == "talk to [alice](/people/alice.md)"
    print("OK 8 rewrite inline links")


def test_9_rewrite_no_resolver_passthrough():
    text = "[[people/alice]]"
    assert rewrite_inline_links(text) == text
    print("OK 9 no resolver leaves text unchanged")


def test_10_scan_session_file():
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "session_x.md"
        p.write_text(
            "---\nname: x\n---\nbody cites [[sessions/y]] and [[people/z]]\n",
            encoding="utf-8",
        )
        info = scan_session_file(p)
        assert info["session_refs"] == ["y"]
        assert info["typed_links"]["people"] == ["z"]
        assert info["raw_count"] == 2
    print("OK 10 scan_session_file")


def test_11_nested_paths():
    text = "[[wiki/sub/dir/deep-page]]"
    entities = extract_entities(text)
    assert len(entities) == 1
    assert entities[0][1] == "sub/dir/deep-page"
    print("OK 11 nested path supported")


def test_12_namespaces_match_spec():
    assert set(VALID_NAMESPACES) == {"wiki", "people", "companies", "concepts", "sessions"}
    print("OK 12 namespaces match SPEC")


if __name__ == "__main__":
    tests = [test_1_extract_basic, test_2_session_refs_filter,
             test_3_invalid_namespace_ignored, test_4_dedup,
             test_5_build_session_links_merge_existing, test_6_build_session_links_md_suffix_normalize,
             test_7_typed_links_grouping, test_8_rewrite_inline_links,
             test_9_rewrite_no_resolver_passthrough, test_10_scan_session_file,
             test_11_nested_paths, test_12_namespaces_match_spec]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} entity_extractor smoke pass")
