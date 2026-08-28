"""v3.2 · COMPASS_CHUNK_RECALL (utterance-routing production port) unit tests.

Function-level: chunk window semantics + RRF fusion wiring. The embedder is
mocked — the BGE-model-dependent e2e is covered by the LongMemEval evidence
chain (docs/evidence/headhead_mem0_full500_20260826.json), not by CI.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["COMPASS_CHUNK_RECALL"] = "1"

import daemon as zmd  # noqa: E402


def test_window2_pairing():
    """short paras pair with their successor (eval window=2 semantics)"""
    body = "A" + "\n\n" + "B" + "\n\n" + "C"
    assert zmd._entry_chunks(body, max_chars=500) == ["A\nB", "B\nC", "C"]


def test_long_para_truncated_not_merged():
    """a para pair over max_chars is truncated, never skipped"""
    body = ("长" * 400) + "\n\n" + ("短" * 20)
    chunks = zmd._entry_chunks(body, max_chars=500)
    assert len(chunks) == 2
    assert all(len(c) <= 500 for c in chunks)
    assert chunks[0].startswith("长")


def test_cap_and_empty():
    assert zmd._entry_chunks("") == []
    body = "\n\n".join(f"p{i}" for i in range(40))
    assert len(zmd._entry_chunks(body)) <= zmd._CHUNK_PER_ENTRY_CAP


def test_rrf_fusion_pulls_chunk_hit_up():
    """an entry ranked #8 by dense but #1 by chunk-best should fuse into top-3"""
    e_a = {"path": "a.md"}
    e_b = {"path": "b.md"}
    e_hit = {"path": "hit.md"}  # dense #8, chunk #1
    dense = [(0.9, e_a), (0.85, e_b)] + [(0.5 - i * 0.01, {"path": f"f{i}.md"}) for i in range(6)] + [(0.4, e_hit)]
    chunk = [(0.95, e_hit), (0.7, e_b)]
    fused = zmd._rrf_fusion([dense, chunk], k=60, top_k=3)
    paths = [e["path"] for _, e in fused]
    assert "hit.md" in paths, paths


def test_flag_default_off():
    """CI env hygiene: default (unset) means the feature is off"""
    import importlib
    for var in ("COMPASS_CHUNK_RECALL",):
        os.environ.pop(var, None)
    importlib.reload(zmd)
    assert zmd._CHUNK_RECALL_USE is False
    os.environ["COMPASS_CHUNK_RECALL"] = "1"
    importlib.reload(zmd)  # restore for other tests in this process


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"  {name} OK")
    print("ALL_CHUNK_TESTS_PASS")
