import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from okf.exporter import build_okf_bundle
from okf.validator import validate_okf_bundle


# ---------------------------------------------------------------------------
# Rule 1: every concept must have a non-empty `type`
# ---------------------------------------------------------------------------

def test_validate_flags_missing_type():
    bundle = {
        "concepts": [
            {"name": "a", "type": "project", "description": ""},
            {"name": "b", "type": "", "description": ""},  # empty type
        ],
        "link_graph": {"a": [], "b": []},
        "backlinks": {},
    }
    errors = validate_okf_bundle(bundle)
    assert len(errors) == 1
    assert "type" in errors[0]
    assert "b" in errors[0]


def test_validate_flags_missing_type_key_entirely():
    bundle = {
        "concepts": [
            {"name": "c", "description": ""},  # no type key at all
        ],
        "link_graph": {"c": []},
        "backlinks": {},
    }
    errors = validate_okf_bundle(bundle)
    assert any("type" in e and "c" in e for e in errors)


# ---------------------------------------------------------------------------
# Rule 2: dangling links (target not a known concept)
# ---------------------------------------------------------------------------

def test_validate_flags_dangling_link():
    bundle = {
        "concepts": [
            {"name": "a", "type": "project", "description": ""},
        ],
        "link_graph": {"a": ["ghost"]},  # ghost is not a known concept
        "backlinks": {"ghost": ["a"]},
    }
    errors = validate_okf_bundle(bundle)
    assert any("ghost" in e for e in errors)
    assert any("a" in e for e in errors)


# ---------------------------------------------------------------------------
# Rule 3: backlink symmetry
# ---------------------------------------------------------------------------

def test_validate_flags_asymmetric_backlink():
    bundle = {
        "concepts": [
            {"name": "a", "type": "project", "description": ""},
            {"name": "b", "type": "reference", "description": ""},
        ],
        "link_graph": {"a": ["b"], "b": []},
        "backlinks": {},  # missing: backlinks[b] should contain a
    }
    errors = validate_okf_bundle(bundle)
    assert len(errors) >= 1
    assert any("a" in e and "b" in e for e in errors)


# ---------------------------------------------------------------------------
# Clean bundle passes
# ---------------------------------------------------------------------------

def test_validate_clean_bundle_passes():
    bundle = {
        "concepts": [
            {"name": "a", "type": "project", "description": ""},
            {"name": "b", "type": "reference", "description": ""},
        ],
        "link_graph": {"a": ["b"], "b": []},
        "backlinks": {"b": ["a"]},
    }
    assert validate_okf_bundle(bundle) == []


# ---------------------------------------------------------------------------
# Robustness: missing keys must not crash
# ---------------------------------------------------------------------------

def test_validate_empty_bundle_does_not_crash():
    assert validate_okf_bundle({}) == []


# ---------------------------------------------------------------------------
# Round-trip against the real exporter (true consumer)
# ---------------------------------------------------------------------------

def test_export_then_validate_roundtrip(tmp_path):
    (tmp_path / "a.md").write_text(
        "---\nname: a\nmetadata:\n  type: project\n---\nlink [[b]]",
        encoding="utf-8",
    )
    (tmp_path / "b.md").write_text(
        "---\nname: b\nmetadata:\n  type: reference\n---\nno links",
        encoding="utf-8",
    )
    bundle = build_okf_bundle(tmp_path)
    assert validate_okf_bundle(bundle) == []        # exported bundle is self-consistent
    assert bundle["backlinks"]["b"] == ["a"]         # consumer: backlink index rebuildable
