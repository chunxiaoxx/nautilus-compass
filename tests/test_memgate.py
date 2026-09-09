"""记忆门三件套单测(#48)· 向量/文件全注入,不依赖 BGE 与生产 daemon。"""
import pytest

import daemon
from session_writer import _inject_frontmatter_field

# ── 修复一 · fact_status 解析 ────────────────────────────────────────────

def test_parse_memory_file_reads_fact_status(tmp_path):
    f = tmp_path / "m.md"
    f.write_text("---\nname: n1\ndescription: d\nfact_status: measured\n"
                 "verified_at: 2026-09-09\n---\n\nbody text\n", encoding="utf-8")
    e = daemon.parse_memory_file(f)
    assert e["fact_status"] == "measured"
    assert e["verified_at"] == "2026-09-09"


def test_parse_memory_file_fact_status_absent_is_empty(tmp_path):
    f = tmp_path / "m.md"
    f.write_text("---\nname: n1\n---\n\nbody\n", encoding="utf-8")
    assert daemon.parse_memory_file(f)["fact_status"] == ""


# ── 修复二 · dedup_verdict 三档(假向量) ─────────────────────────────────

def _ent(path, vec):
    return {"path": path, "embedding": vec}


def test_dedup_merge_hit():
    q = [1.0, 0.0]
    ents = [_ent("a.md", [0.99, 0.1]), _ent("far.md", [0.0, 1.0])]
    r = daemon.dedup_verdict(q, ents)
    assert r["verdict"] == "merge"
    assert r["hits"][0]["path"] == "a.md"


def test_dedup_gray_zone():
    # cosine ≈ 0.8(在 gray 0.75-0.9)
    q = [1.0, 0.0]
    ents = [_ent("g.md", [0.8, 0.6])]  # cos = 0.8
    assert daemon.dedup_verdict(q, ents)["verdict"] == "gray"


def test_dedup_unique_no_hits():
    q = [1.0, 0.0]
    ents = [_ent("x.md", [0.0, 1.0]), _ent("y.md", [-1.0, 0.0])]
    r = daemon.dedup_verdict(q, ents)
    assert r["verdict"] == "unique" and r["hits"] == []


def test_dedup_entries_without_embedding_skipped():
    q = [1.0, 0.0]
    ents = [{"path": "noemb.md"}, _ent("x.md", [0.0, 1.0])]
    assert daemon.dedup_verdict(q, ents)["verdict"] == "unique"


# ── 修复三 · 沿链一跳 ────────────────────────────────────────────────────

def _entry(path, name, desc="", body=""):
    return {"path": path, "name": name, "description": desc, "body": body,
            "fact_status": "", "age_str": "1d", "age_seconds": 86400}


def test_chain_expand_one_hop():
    a = _entry("a.md", "anchor-a", body="见 [[b-rule]] 的细节")
    b = _entry("b-rule.md", "b-rule", desc="被引用的条目")
    c = _entry("c.md", "c-other", body="无链")
    out = daemon.expand_chain_links([(0.9, a)], [a, b, c])
    assert len(out) == 1
    assert out[0]["path"] == "b-rule.md"
    assert out[0]["via"] == "a.md"


def test_chain_expand_no_links_empty():
    a = _entry("a.md", "a", body="普通正文无链接")
    assert daemon.expand_chain_links([(0.9, a)], [a]) == []


def test_chain_expand_skips_already_in_top():
    a = _entry("a.md", "a", body="见 [[b-rule]]")
    b = _entry("b-rule.md", "b-rule")
    assert daemon.expand_chain_links([(0.9, a), (0.8, b)], [a, b]) == []


def test_chain_expand_cap():
    a = _entry("a.md", "a", body=" ".join(f"[[t{i}]]" for i in range(10)))
    entries = [a] + [_entry(f"t{i}.md", f"t{i}") for i in range(10)]
    assert len(daemon.expand_chain_links([(0.9, a)], entries, cap=3)) == 3


def test_chain_expand_dangling_link_ignored():
    a = _entry("a.md", "a", body="引用 [[ghost]] 不存在")
    assert daemon.expand_chain_links([(0.9, a)], [a]) == []


def test_chain_expand_no_recursion():
    """a→b→c:命中 a 只展开 b,c 不跟(b 不在 top,但其链不被走)。"""
    a = _entry("a.md", "a", body="见 [[b-rule]]")
    b = _entry("b-rule.md", "b-rule", body="见 [[c-deep]]")
    c = _entry("c-deep.md", "c-deep")
    out = daemon.expand_chain_links([(0.9, a)], [a, b, c])
    assert [o["path"] for o in out] == ["b-rule.md"]


# ── session_writer · frontmatter 注入 ───────────────────────────────────

def test_inject_field_into_existing_frontmatter():
    md = "---\nname: n\n---\n\nbody\n"
    out = _inject_frontmatter_field(md, "merge_target", "old.md#0.93")
    assert "merge_target: old.md#0.93" in out
    assert out.index("merge_target") < out.index("---", 4)


def test_inject_field_without_frontmatter():
    out = _inject_frontmatter_field("body only", "merge_target", "x.md#0.9")
    assert out.startswith("---\nmerge_target: x.md#0.9\n---\n")
    assert "body only" in out


# ── schema 防线 · fact_status 值域(纪律的可执行部分) ────────────────────

FACT_STATUSES = {"measured", "inferred", "heard"}


def test_fact_status_value_domain():
    """J1 支撑:字段值必须落三档。"""
    assert FACT_STATUSES == {"measured", "inferred", "heard"}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
