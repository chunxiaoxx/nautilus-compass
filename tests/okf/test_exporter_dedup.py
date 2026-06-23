"""Regression: duplicate `name:` across memory files must be handled losslessly.

Found by v2.3.0 final code review on the real library (21 names appear in
multiple files). Before the fix, a later file overwrote the earlier file's
link_graph entry while its backlinks survived — a silent asymmetry. The
exporter now dedups concepts by name and unions outgoing links.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from okf.exporter import build_okf_bundle


def test_duplicate_name_dedup_and_link_union(tmp_path):
    (tmp_path / "a.md").write_text(
        "---\nname: dup\nmetadata:\n  type: project\n---\nlink [[x]]",
        encoding="utf-8",
    )
    (tmp_path / "b.md").write_text(
        "---\nname: dup\nmetadata:\n  type: reference\n---\nlink [[y]]",
        encoding="utf-8",
    )
    bundle = build_okf_bundle(tmp_path)
    names = [c["name"] for c in bundle["concepts"]]
    assert names.count("dup") == 1                       # deduped to one concept
    assert set(bundle["link_graph"]["dup"]) == {"x", "y"}  # links unioned, none dropped
    assert bundle["backlinks"]["x"] == ["dup"]           # symmetry preserved
    assert bundle["backlinks"]["y"] == ["dup"]


def test_duplicate_name_same_target_no_double(tmp_path):
    (tmp_path / "a.md").write_text(
        "---\nname: dup\nmetadata:\n  type: project\n---\n[[x]]", encoding="utf-8",
    )
    (tmp_path / "b.md").write_text(
        "---\nname: dup\nmetadata:\n  type: project\n---\n[[x]]", encoding="utf-8",
    )
    bundle = build_okf_bundle(tmp_path)
    assert bundle["link_graph"]["dup"] == ["x"]          # de-duped within union
    assert bundle["backlinks"]["x"] == ["dup"]
