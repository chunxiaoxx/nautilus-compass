import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from okf.exporter import build_okf_bundle
from okf.validator import validate_okf_bundle, find_dangling_links


# ---------------------------------------------------------------------------
# Hard rule 1: every concept must have a non-empty `type`
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
# Dangling links = legitimate forward references (compass memory convention:
# "a [[name]] that doesn't match an existing memory yet is fine; it marks
# something worth writing later, not an error"). validate() ignores them;
# find_dangling_links() reports them as informational signal.
# ---------------------------------------------------------------------------

def test_validate_ignores_dangling_link():
    bundle = {
        "concepts": [
            {"name": "a", "type": "project", "description": ""},
        ],
        "link_graph": {"a": ["ghost"]},          # ghost = forward ref (no concept yet)
        "backlinks": {"ghost": ["a"]},           # exporter keeps backlink symmetric even for forward-refs
    }
    assert validate_okf_bundle(bundle) == []     # forward ref is NOT a hard error


def test_find_dangling_links_reports_forward_refs():
    bundle = {
        "concepts": [
            {"name": "a", "type": "project", "description": ""},
        ],
        "link_graph": {"a": ["ghost"]},
        "backlinks": {"ghost": ["a"]},
    }
    dangling = find_dangling_links(bundle)
    assert any("ghost" in d for d in dangling)
    assert any("a" in d for d in dangling)


def test_find_dangling_links_empty_when_all_resolve():
    bundle = {
        "concepts": [
            {"name": "a", "type": "project", "description": ""},
            {"name": "b", "type": "reference", "description": ""},
        ],
        "link_graph": {"a": ["b"]},
        "backlinks": {"b": ["a"]},
    }
    assert find_dangling_links(bundle) == []


# ---------------------------------------------------------------------------
# Hard rule 2: backlink symmetry
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
    assert find_dangling_links({}) == []


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
    assert find_dangling_links(bundle) == []         # all links resolve within the export
    assert bundle["backlinks"]["b"] == ["a"]         # consumer: backlink index rebuildable
