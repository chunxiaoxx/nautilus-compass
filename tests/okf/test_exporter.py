import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from okf.exporter import parse_memory_frontmatter, extract_wikilinks, build_okf_bundle


# ---------------------------------------------------------------------------
# parse_memory_frontmatter
# ---------------------------------------------------------------------------

def test_parse_frontmatter_basic_fields_and_type_promotion():
    md = """---
name: alpha
description: First memory
metadata:
  type: reference
---
Body text here.
"""
    fm, body = parse_memory_frontmatter(md)
    assert fm["name"] == "alpha"
    assert fm["description"] == "First memory"
    # metadata.type promoted to top-level `type` (OKF required field)
    assert fm["type"] == "reference"
    assert body.strip() == "Body text here."


def test_parse_frontmatter_no_frontmatter_returns_empty_dict():
    md = "Just a body, no frontmatter.\nLine two."
    fm, body = parse_memory_frontmatter(md)
    assert fm == {}
    assert body == md


def test_parse_frontmatter_bad_block_does_not_crash():
    # An opening --- but no closing --- should not raise.
    md = "---\nname: broken\nstill no closing fence\nmore lines"
    fm, body = parse_memory_frontmatter(md)
    assert isinstance(fm, dict)
    assert isinstance(body, str)


def test_parse_frontmatter_metadata_flat_key():
    # metadata.type written as a flat dotted key also promotes.
    md = """---
name: beta
description: flat style
metadata.type: project
---
body
"""
    fm, _ = parse_memory_frontmatter(md)
    assert fm["type"] == "project"


# ---------------------------------------------------------------------------
# extract_wikilinks
# ---------------------------------------------------------------------------

def test_extract_wikilinks_dedup_preserve_order():
    body = "see [[a]] and [[b-c]] and [[a]]"
    assert extract_wikilinks(body) == ["a", "b-c"]


def test_extract_wikilinks_none():
    assert extract_wikilinks("no links here") == []


def test_extract_wikilinks_strips_whitespace():
    assert extract_wikilinks("[[ spaced ]] and [[x]]") == ["spaced", "x"]


# ---------------------------------------------------------------------------
# build_okf_bundle
# ---------------------------------------------------------------------------

def _write(p, text):
    p.write_text(text, encoding="utf-8")


def test_build_bundle_concepts_links_and_backlinks(tmp_path):
    _write(tmp_path / "a.md", """---
name: a
description: Concept A
metadata:
  type: reference
---
A points to [[b]].
""")
    _write(tmp_path / "b.md", """---
name: b
description: Concept B
metadata:
  type: project
---
B points back to [[a]].
""")

    bundle = build_okf_bundle(tmp_path)

    concepts = {c["name"]: c for c in bundle["concepts"]}
    assert set(concepts) == {"a", "b"}
    # every concept has a type
    assert all("type" in c for c in bundle["concepts"])
    assert concepts["a"]["type"] == "reference"
    assert concepts["b"]["type"] == "project"
    assert concepts["a"]["description"] == "Concept A"

    # directed link graph
    assert bundle["link_graph"]["a"] == ["b"]
    assert bundle["link_graph"]["b"] == ["a"]

    # backlinks are symmetric to links: a->b means backlinks[b] contains a
    assert bundle["backlinks"]["b"] == ["a"]
    assert bundle["backlinks"]["a"] == ["b"]


def test_build_bundle_skips_non_md_and_nameless(tmp_path):
    _write(tmp_path / "good.md", """---
name: good
description: ok
metadata:
  type: user
---
body
""")
    _write(tmp_path / "nameless.md", """---
description: no name field
metadata:
  type: user
---
body
""")
    _write(tmp_path / "notes.txt", "name: ignored")

    bundle = build_okf_bundle(tmp_path)
    names = {c["name"] for c in bundle["concepts"]}
    assert names == {"good"}


def test_build_bundle_accepts_str_path(tmp_path):
    _write(tmp_path / "x.md", """---
name: x
description: d
metadata:
  type: reference
---
body
""")
    bundle = build_okf_bundle(str(tmp_path))
    assert [c["name"] for c in bundle["concepts"]] == ["x"]


def test_build_bundle_backlinks_dedup_preserve_order(tmp_path):
    # two sources both link to target -> backlinks[target] preserves source order, deduped
    _write(tmp_path / "t.md", """---
name: t
description: target
metadata:
  type: reference
---
no outgoing
""")
    _write(tmp_path / "s1.md", """---
name: s1
description: source one
metadata:
  type: reference
---
link [[t]] and again [[t]]
""")
    _write(tmp_path / "s2.md", """---
name: s2
description: source two
metadata:
  type: reference
---
link [[t]]
""")
    bundle = build_okf_bundle(tmp_path)
    assert bundle["backlinks"]["t"] == ["s1", "s2"]
    assert bundle["link_graph"]["s1"] == ["t"]
