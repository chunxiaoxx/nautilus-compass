"""Memory cache behavior with a failed Mac watcher; no model or daemon starts."""
from __future__ import annotations

import os
import sys
import time
from types import ModuleType, SimpleNamespace

import pytest

import daemon as d


@pytest.fixture
def memory_env(tmp_path, monkeypatch):
    clock = SimpleNamespace(wall=1_800_000_000.0, monotonic=1000.0)
    monkeypatch.setattr(d, "time", SimpleNamespace(
        time=lambda: clock.wall, monotonic=lambda: clock.monotonic,
        strftime=time.strftime, gmtime=time.gmtime,
    ))
    monkeypatch.setattr(d.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(d, "_ENTRIES_CACHE", {})
    monkeypatch.setattr(d, "_ENTRIES_CACHE_META", {}, raising=False)
    monkeypatch.setattr(d, "_ENTRIES_CACHE_TTL", 5.0, raising=False)
    monkeypatch.setattr(d, "_DIR_DIRTY", set())
    monkeypatch.setattr(d, "_RECALL_CACHE", d._OrderedDict_p9())
    monkeypatch.setattr(d, "_RECALL_CACHE_STATS", dict(hit=0, miss=0, expire=0, evict=0))
    monkeypatch.setattr(d, "_state", {**d._state, "memory_caches": {}})
    monkeypatch.setattr(d, "_INOTIFY_USE", True)
    monkeypatch.setattr(d, "_INOTIFY_STATS", dict(
        events=0, rescans_avoided=0, rescans_done=0, watch_count=0, errors=0))
    for flag in ("_PROD_RERANK_USE", "_PROD_LIFECYCLE_USE", "_CHUNK_RECALL_USE",
                 "_BM25_RRF_USE", "_PROD_QUERY_REWRITE_USE", "_PROD_TIER_WEIGHT_USE"):
        monkeypatch.setattr(d, flag, False)
    monkeypatch.setattr(d, "_flush_memory_pkl", lambda *_: None)
    monkeypatch.setattr(d, "_p9_maybe_log_stats", lambda: None)
    monkeypatch.setattr(d, "_inotify_maybe_log_stats", lambda: None)
    monkeypatch.setattr(d, "log", lambda *_: None)
    monkeypatch.setattr(d, "CACHE_DIR", tmp_path / "cache")
    d.CACHE_DIR.mkdir()
    encoded = []

    def encode(texts):
        if isinstance(texts, str):
            encoded.append(texts)
            return [1.0, 0.0]
        encoded.extend(texts)
        return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(d, "get_embedder", lambda: SimpleNamespace(encode=encode))
    # Exercise the real failure branch without starting a watcher thread.
    fake = ModuleType("inotify_simple")

    def unsupported():
        raise OSError("inotify_init1: symbol not found (Mac fixture)")

    fake.INotify = unsupported
    fake.flags = SimpleNamespace()
    monkeypatch.setitem(sys.modules, "inotify_simple", fake)
    d._inotify_watcher_thread()
    assert d._INOTIFY_STATS["watch_count"] == 0
    project = "cache-fixture"
    memory = tmp_path / ".claude" / "projects" / project / "memory"
    memory.mkdir(parents=True)

    def write(name, body="original", age=0):
        p = memory / name
        p.write_text(f"---\nname: {p.stem}\ndescription: fixture\n---\n{body}")
        stamp = clock.wall - age
        os.utime(p, (stamp, stamp))
        return p

    def advance(seconds):
        clock.wall += seconds
        clock.monotonic += seconds

    def recall():
        return d.handle_request(dict(action="recall", query="fixture target",
                                     project=project, top_k=1))

    return SimpleNamespace(memory=memory, write=write, advance=advance,
                           clock=clock, encoded=encoded, recall=recall)


@pytest.mark.parametrize("change", ["add", "modify", "delete"])
def test_failed_watcher_sees_changes_by_refresh_deadline(memory_env, change):
    e = memory_env
    e.write("a.md")
    b = e.write("b.md")
    assert {x["path"] for x in d.get_memory_entries(e.memory)} == {"a.md", "b.md"}
    e.advance(6)
    if change == "add":
        e.write("c.md")
    elif change == "modify":
        e.write("a.md", "updated")
    else:
        b.unlink()
    rows = {x["path"]: x for x in d.get_memory_entries(e.memory)}
    if change == "modify":
        assert rows["a.md"]["body"] == "updated"
        assert sum("updated" in text for text in e.encoded) == 1
    else:
        assert set(rows) == ({"a.md", "b.md", "c.md"} if change == "add" else {"a.md"})


@pytest.mark.parametrize("change", ["add", "delete"])
def test_directory_mtime_detects_add_delete_before_ttl(memory_env, change):
    e = memory_env
    e.write("a.md")
    b = e.write("b.md")
    d.get_memory_entries(e.memory)
    before = e.memory.stat().st_mtime_ns
    if change == "add":
        e.write("c.md")
    else:
        b.unlink()
    # Explicit nanosecond change makes the fixture independent of FS resolution.
    os.utime(e.memory, ns=(before + 1_000_000, before + 1_000_000))
    expected = {"a.md", "b.md", "c.md"} if change == "add" else {"a.md"}
    assert {x["path"] for x in d.get_memory_entries(e.memory)} == expected


def test_cache_hit_recomputes_age_without_reembedding(memory_env):
    e = memory_env
    e.write("a.md", age=86399)
    first = d.get_memory_entries(e.memory)
    encoded_before = len(e.encoded)
    e.advance(2)
    second = d.get_memory_entries(e.memory)
    assert second[0]["age_seconds"] == 86401
    assert second[0]["age_str"] == "1d"
    assert first[0]["age_seconds"] == 86399  # avoid mutating another caller's rows
    assert len(e.encoded) == encoded_before


def test_disabled_watcher_keeps_bounded_cache_and_refreshes(memory_env, monkeypatch):
    e = memory_env
    monkeypatch.setattr(d, "_INOTIFY_USE", False)
    e.write("a.md")
    parsed = []
    original_parse = d.parse_memory_file

    def counted(p):
        parsed.append(p)
        return original_parse(p)

    monkeypatch.setattr(d, "parse_memory_file", counted)
    d.get_memory_entries(e.memory)
    e.advance(1)
    d.get_memory_entries(e.memory)
    assert len(parsed) == 1
    e.advance(5)
    e.write("a.md", "updated")
    assert d.get_memory_entries(e.memory)[0]["body"] == "updated"


@pytest.mark.parametrize("change", ["add", "modify", "delete"])
def test_same_query_result_cache_cannot_mask_directory_refresh(memory_env, change):
    e = memory_env
    a = e.write("a.md")
    first = e.recall()
    assert first["ok"] and first["recall"][0]["body"] == "original"
    e.advance(6)
    if change == "add":
        e.write("0-new.md", "new entry")
    elif change == "modify":
        e.write("a.md", "updated")
    else:
        a.unlink()
    second = e.recall()
    assert not second.get("from_cache")
    if change == "add":
        assert second["recall"][0]["path"] == "0-new.md"
    elif change == "modify":
        assert second["recall"][0]["body"] == "updated"
    else:
        assert second["recall"] == []


def test_cached_result_drops_expired_fresh_extra(memory_env):
    e = memory_env
    e.write("a-old.md", age=172800)
    e.write("z-recent.md", age=86399)
    first = e.recall()
    assert [x["path"] for x in first["fresh_extra"]] == ["z-recent.md"]
    e.advance(2)
    second = e.recall()
    assert second.get("from_cache") is True
    assert second["fresh_extra"] == []
    assert second["recall"][0]["age_seconds"] == 172802
    assert len(first["fresh_extra"]) == 1


def test_dirty_event_invalidates_same_query_before_ttl(memory_env):
    e = memory_env
    e.write("a.md")
    e.recall()
    e.advance(1)
    e.write("a.md", "updated")
    d._DIR_DIRTY.add(str(e.memory))
    second = e.recall()
    assert not second.get("from_cache")
    assert second["recall"][0]["body"] == "updated"


def test_other_query_refresh_does_not_revalidate_an_old_result(memory_env):
    e = memory_env
    e.write("a.md")
    e.recall()
    e.advance(6)
    e.write("a.md", "updated")
    other = d.handle_request(dict(action="recall", query="different fixture query",
                                  project="cache-fixture", top_k=1))
    assert other["recall"][0]["body"] == "updated"
    original_query = e.recall()
    assert original_query["recall"][0]["body"] == "updated"
    assert not original_query.get("from_cache")
