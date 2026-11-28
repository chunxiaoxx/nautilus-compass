"""向量缓存按内容判有效(daemon_v33)· 2026-11-28。

现象(云上实测):MCP 每次召回后都会改写命中的记忆文件(文件头里的命中计数 +1),文件 mtime 随之变化;
向量缓存只按 (路径, mtime) 判有效,于是这几个文件的整段向量与分块向量被全部重算,
云端 CPU 上单次 20–30 秒——线上"连续两次不同查询,第二次必慢"的根本原因。

改法:每条缓存同时记一份"嵌入文本的内容指纹"。mtime 变了但指纹没变(只改了文件头),向量直接复用。
本文件钉住主用例,并带阴性对照:正文或描述变了必须重算、换了嵌入模型必须重算、
旧格式缓存 mtime 对不上时首次仍要重算。
"""
from __future__ import annotations

import hashlib
import os
import pickle
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import daemon_v33 as d  # noqa: E402


def _vec(row):
    vector = row["embedding"]
    return vector.tolist() if hasattr(vector, "tolist") else list(vector)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("COMPASS_RETRIEVAL_SKIP_RE", raising=False)
    monkeypatch.setattr(d.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(d, "_state", {**d._state, "memory_caches": {}})
    monkeypatch.setattr(d, "_CONTENT_HASHES", {}, raising=False)
    monkeypatch.setattr(d, "_ENTRIES_CACHE", d._OrderedDict_p9())
    monkeypatch.setattr(d, "_DIR_DIRTY", set())
    monkeypatch.setattr(d, "_MEM_LOCKS", {})
    monkeypatch.setattr(d, "_RECALL_CACHE", d._OrderedDict_p9())
    monkeypatch.setattr(d, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(d, "_INOTIFY_USE", False)
    monkeypatch.setattr(d, "_INOTIFY_STATS", dict(
        events=0, rescans_avoided=0, rescans_done=0, watch_count=0, errors=0))
    for flag in ("_PROD_RERANK_USE", "_PROD_LIFECYCLE_USE", "_CHUNK_RECALL_USE",
                 "_BM25_RRF_USE", "_PROD_QUERY_REWRITE_USE", "_PROD_TIER_WEIGHT_USE"):
        monkeypatch.setattr(d, flag, False)
    monkeypatch.setattr(d, "_retrieval_skip_pattern", lambda: False)
    monkeypatch.setattr(d, "_inotify_maybe_log_stats", lambda: None)
    monkeypatch.setattr(d, "_p9_cache_get", lambda key: None)
    monkeypatch.setattr(d, "_p9_cache_put", lambda key, result: None)
    monkeypatch.setattr(d, "log", lambda *_: None)
    d.CACHE_DIR.mkdir()
    encoded = []

    def encode(text):
        encoded.append(text)
        return [float(len(text)), 1.0]  # 向量随文本变化:重算与否、算的是哪份文本,都能断言

    monkeypatch.setattr(d, "get_embedder", lambda: SimpleNamespace(encode=encode))
    project = "hash-fixture"
    memory = tmp_path / ".claude" / "projects" / project / "memory"
    memory.mkdir(parents=True)
    base = time.time() - 10_000

    def write(name, body="original body", front=(), stamp=0, description="fixture"):
        path = memory / name
        extra = "".join(f"{key}: {value}\n" for key, value in front)
        path.write_text(f"---\nname: {path.stem}\ndescription: {description}\n{extra}---\n{body}",
                        encoding="utf-8")
        stamp_at = base + stamp
        os.utime(path, (stamp_at, stamp_at))
        return path

    return SimpleNamespace(memory=memory, project=project, write=write, encoded=encoded, base=base)


# ── 主用例 ──────────────────────────────────────────────────────────────────

def test_frontmatter_only_rewrite_reuses_vector(env):
    """命中加成只改文件头:向量照用,不算第二次。"""
    env.write("a.md", stamp=0)
    first = d.get_memory_entries(env.memory)
    assert len(env.encoded) == 1
    env.write("a.md", stamp=10, front=[("reinforce_count", "1")])
    second = d.get_memory_entries(env.memory)
    assert len(env.encoded) == 1
    assert _vec(second[0]) == _vec(first[0])


def test_unchanged_file_is_not_reencoded(env):
    """对照:文件没动时不重算(原有行为不变)。"""
    env.write("a.md", stamp=0)
    first = d.get_memory_entries(env.memory)
    second = d.get_memory_entries(env.memory)
    assert len(env.encoded) == 1
    assert _vec(second[0]) == _vec(first[0])


def test_recall_after_hit_rewrite_encodes_only_the_query(env, monkeypatch):
    """端到端复现线上时序:召回 → 命中文件被改写 → 项目标脏 → 再召回,只应算查询向量。"""
    monkeypatch.setattr(d, "_INOTIFY_USE", True)
    bodies = {f"m{i}.md": f"memory number {i} body" for i in range(3)}
    for i, name in enumerate(bodies):
        env.write(name, bodies[name], stamp=i)
    first = d.handle_request(dict(action="recall", query="query one", project=env.project, top_k=3))
    assert first["ok"] and len(first["recall"]) == 3
    assert len(env.encoded) == 3 + 1  # 3 条记忆 + 1 条查询
    for i, hit in enumerate(first["recall"]):
        env.write(hit["path"], bodies[hit["path"]], stamp=100 + i, front=[("reinforce_count", "1")])
    d._DIR_DIRTY.add(str(env.memory))
    second = d.handle_request(dict(action="recall", query="query two", project=env.project, top_k=3))
    assert second["ok"] and len(second["recall"]) == 3
    assert len(env.encoded) == 3 + 1 + 1


# ── 阴性对照:该重算的必须重算 ────────────────────────────────────────────────

def test_body_change_reembeds(env):
    env.write("a.md", stamp=0)
    first = d.get_memory_entries(env.memory)
    env.write("a.md", "a different and longer body", stamp=10)
    second = d.get_memory_entries(env.memory)
    assert len(env.encoded) == 2
    assert _vec(second[0]) != _vec(first[0])
    assert env.encoded[-1] == "fixture\na different and longer body"


def test_description_change_reembeds(env):
    env.write("a.md", stamp=0)
    d.get_memory_entries(env.memory)
    env.write("a.md", stamp=10, description="a new description")
    d.get_memory_entries(env.memory)
    assert len(env.encoded) == 2


def test_embedder_model_change_invalidates_content_match(env, monkeypatch):
    env.write("a.md", stamp=0)
    d.get_memory_entries(env.memory)
    monkeypatch.setattr(d, "EMBEDDER_MODEL", "some-other-embedding-model")
    env.write("a.md", stamp=10, front=[("reinforce_count", "1")])
    d.get_memory_entries(env.memory)
    assert len(env.encoded) == 2


def test_old_format_cache_with_stale_mtime_reembeds_once(env):
    """旧格式缓存没有指纹:mtime 对不上时无法证明内容相同,首次照旧重算;之后只改文件头不再重算。"""
    a = env.write("a.md", stamp=0)
    _write_pkl(env.memory, {str(a): (env.base - 5_000, [7.0, 7.0])})
    d.get_memory_entries(env.memory)
    assert len(env.encoded) == 1
    env.write("a.md", stamp=10, front=[("reinforce_count", "1")])
    d.get_memory_entries(env.memory)
    assert len(env.encoded) == 1


# ── 指纹的补记与持久化 ──────────────────────────────────────────────────────

def test_matching_mtime_backfills_fingerprint_without_reencoding(env):
    """旧格式缓存 mtime 对得上:不算向量,但把指纹补上,于是下一次只改文件头也不用重算。"""
    a = env.write("a.md", stamp=0)
    _write_pkl(env.memory, {str(a): (a.stat().st_mtime, [float(len("fixture\noriginal body")), 1.0])})
    d.get_memory_entries(env.memory)
    assert len(env.encoded) == 0
    env.write("a.md", stamp=10, front=[("reinforce_count", "1")])
    d.get_memory_entries(env.memory)
    assert len(env.encoded) == 0


def test_fingerprints_survive_pkl_roundtrip(env):
    """项目被逐出或守护进程重启后,内存里的指纹没了,要从盘上回读。"""
    env.write("a.md", stamp=0)
    d.get_memory_entries(env.memory)
    d._state["memory_caches"].pop(str(env.memory), None)
    d._CONTENT_HASHES.pop(str(env.memory), None)
    env.write("a.md", stamp=10, front=[("reinforce_count", "1")])
    d.get_memory_entries(env.memory)
    assert len(env.encoded) == 1


def test_fingerprint_of_deleted_file_is_pruned_with_its_vector(env):
    env.write("a.md", stamp=0)
    gone = env.write("gone.md", stamp=0)
    d.get_memory_entries(env.memory)
    hashes = d._CONTENT_HASHES[str(env.memory)]
    assert str(gone) in hashes
    gone.unlink()
    d.get_memory_entries(env.memory)
    assert str(gone) not in hashes
    assert str(gone) not in d._state["memory_caches"][str(env.memory)]


# ── 分块向量走同一套规则 ────────────────────────────────────────────────────

def test_frontmatter_only_rewrite_reuses_chunk_vectors(env, monkeypatch):
    monkeypatch.setattr(d, "_CHUNK_RECALL_USE", True)
    env.write("a.md", "para one\n\npara two\n\npara three", stamp=0)
    first = d.get_memory_entries(env.memory)
    assert len(env.encoded) == 1 + 3
    env.write("a.md", "para one\n\npara two\n\npara three", stamp=10, front=[("reinforce_count", "1")])
    second = d.get_memory_entries(env.memory)
    assert len(env.encoded) == 4
    assert len(second[0]["chunk_embs"]) == 3
    env.write("a.md", "para one changed\n\npara two\n\npara three\n\npara four", stamp=20)
    d.get_memory_entries(env.memory)
    assert len(env.encoded) == 4 + 1 + 4


def _write_pkl(memory: Path, embeddings: dict) -> None:
    proj_hash = hashlib.sha256(str(memory).encode()).hexdigest()[:12]
    (d.CACHE_DIR / f"{proj_hash}.pkl").write_bytes(pickle.dumps({"embeddings": embeddings}))
