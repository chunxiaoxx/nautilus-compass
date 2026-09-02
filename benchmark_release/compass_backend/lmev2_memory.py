"""Compass memory backend for LongMemEval-V2.

Port of the nautilus-compass retrieval stack (the LongMemEval-S P@1 0.890
weapon) onto the official LME-V2 Memory interface:

- per-state sliding-window chunks (window=2, aligned with our eval semantics;
  greedy packing was tried upstream and re-diluted the signal)
- local BGE-m3 dense embeddings — no LLM extraction, no data egress
- BM25 + dense RRF fusion (hybrid carries ms/tr-type queries that dense drops)
- evidence returns text items plus trajectory screenshots

Black-box contract respected: `query` sees only the question text (and the
optional question screenshot, which this v1 backend ignores — text-only
retrieval), never any benchmark metadata.
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import numpy as np

from .memory import Memory, MemoryContextItem, register_memory

_WORD_RE = re.compile(r"[\w:]+")
# 刀2 · UI 树剪枝:丢无文本的结构行("[20] navigation ''"),保留带内容的行
_A11Y_NOISE_RE = re.compile(r"\[\d+\] \w+ ''")


def _prune_a11y(a11y: str, max_chars: int) -> str:
    lines = [ln for ln in a11y.splitlines() if not _A11Y_NOISE_RE.search(ln)]
    return "\n".join(lines)[:max_chars]


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _state_text(state: dict[str, Any], max_chars: int) -> str:
    url = str(state.get("url") or "")
    action = str(state.get("action") or "")
    thought = str(state.get("thought") or "")
    a11y = _prune_a11y(str(state.get("accessibility_tree") or ""), 500)
    parts = []
    if url:
        parts.append(f"url: {url}")
    if action:
        parts.append(f"action: {action}")
    if thought:
        parts.append(f"thought: {thought}")
    if a11y:
        parts.append(f"page: {a11y}")
    text = " | ".join(parts).strip()
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


@register_memory
class CompassMemory(Memory):
    """Chunked hybrid (dense + BM25, RRF-fused) black-box memory."""

    memory_type = "compass_chunk_hybrid"

    def __init__(self, memory_params: dict[str, object]) -> None:
        super().__init__(memory_params)
        p = self.memory_params
        self._top_k = int(p.get("top_k", 8))
        self._window = max(1, int(p.get("window", 2)))
        self._max_state_chars = int(p.get("max_state_chars", 1200))
        self._max_screenshots = int(p.get("max_screenshots", 4))
        self._text_budget = int(p.get("text_budget_chars", 24000))
        self._per_traj_extra = int(p.get("per_traj_extra", 4))
        self._rrf_k = int(p.get("rrf_k", 60))
        self._model_name = str(p.get("model_name", "BAAI/bge-m3"))
        self._device = str(p.get("device", "cpu"))
        # index state
        self._chunks: list[dict[str, Any]] = []
        self._trajs: dict[str, dict[str, Any]] = {}
        self._matrix: np.ndarray | None = None
        self._bm25_corpus: list[list[str]] = []
        self._bm25_avgdl = 0.0
        self._bm25_df: dict[str, int] = {}
        self._embedder = None

    # ------------------------------------------------------------------ embed
    def _lazy_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(
                self._model_name, device=self._device
            )
        return self._embedder

    def _embed(self, texts: list[str]) -> np.ndarray:
        model = self._lazy_embedder()
        vecs = model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype=np.float32)

    # ----------------------------------------------------------------- insert
    def insert(self, trajectory: dict[str, object]) -> None:
        traj_id = str(trajectory.get("id") or f"traj_{len(self._trajs)}")
        goal = str(trajectory.get("goal") or "")
        outcome = str(trajectory.get("outcome") or "")
        environment = str(trajectory.get("environment") or "")
        states = trajectory.get("states") or []
        self._trajs[traj_id] = {
            "id": traj_id,
            "goal": goal,
            "outcome": outcome,
            "environment": environment,
        }
        texts: list[str] = []
        for st in states:
            if not isinstance(st, dict):
                continue
            t = _state_text(st, self._max_state_chars)
            if t:
                texts.append(t)
        # sliding-window pairing (window=2 -> s_i + s_{i+1}); a lone long
        # state stays its own chunk, never skipped
        units: list[tuple[int, str]] = []
        for i, t in enumerate(texts):
            nxt = texts[i + 1] if i + 1 < len(texts) else ""
            chunk = f"{t}\n{nxt}" if nxt and len(f"{t}\n{nxt}") <= 2 * self._max_state_chars else t
            units.append((i, chunk))
        for i, chunk in units:
            st = states[i] if i < len(states) else {}
            self._chunks.append(
                {
                    "traj_id": traj_id,
                    "state_idx": i,
                    "text": chunk,
                    "screenshot": (st or {}).get("screenshot"),
                }
            )
            self._bm25_corpus.append(_tokenize(chunk))
        self._matrix = None  # invalidate, re-embed lazily on next query
        self._bm25_avgdl = 0.0  # rebuilt lazily

    # ------------------------------------------------------------------ bm25
    def _ensure_bm25(self) -> None:
        if self._bm25_avgdl > 0 or not self._bm25_corpus:
            return
        df: dict[str, int] = {}
        for doc in self._bm25_corpus:
            for tok in set(doc):
                df[tok] = df.get(tok, 0) + 1
        self._bm25_df = df
        total = sum(len(d) for d in self._bm25_corpus)
        self._bm25_avgdl = (total / len(self._bm25_corpus)) if self._bm25_corpus else 1.0

    def _bm25_scores(self, query: str) -> list[float]:
        self._ensure_bm25()
        n = len(self._bm25_corpus)
        if n == 0:
            return []
        k1, b = 1.5, 0.75
        q_tokens = _tokenize(query)
        scores = [0.0] * n
        avgdl = self._bm25_avgdl or 1.0
        for qt in q_tokens:
            df = self._bm25_df.get(qt, 0)
            if df == 0:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            for i, doc in enumerate(self._bm25_corpus):
                tf = doc.count(qt)
                if tf == 0:
                    continue
                denom = tf + k1 * (1 - b + b * len(doc) / avgdl)
                scores[i] += idf * tf * (k1 + 1) / denom
        return scores

    # ------------------------------------------------------------------ index
    def _ensure_matrix(self) -> None:
        if self._matrix is not None or not self._chunks:
            return
        texts = [c["text"] for c in self._chunks]
        self._matrix = self._embed(texts)

    # ----------------------------------------------------------------- query
    def query(
        self,
        query: str,
        query_image: str | None = None,
    ) -> list[MemoryContextItem]:
        if not self._chunks:
            return []
        self._ensure_matrix()
        qv = self._embed([query])[0]
        dense = (self._matrix @ qv).tolist()
        lexical = self._bm25_scores(query)

        def _rrf(rankings: list[list[float]]) -> list[float]:
            fused = [0.0] * len(self._chunks)
            for scores in rankings:
                order = sorted(range(len(scores)), key=lambda i: -scores[i])
                for rank, idx in enumerate(order[:200]):
                    fused[idx] += 1.0 / (self._rrf_k + rank + 1)
            return fused

        fused = _rrf([dense, lexical])
        order = sorted(range(len(fused)), key=lambda i: -fused[i])
        picked = [self._chunks[i] for i in order[: self._top_k]]

        # group by trajectory, keep state order inside each group
        by_traj: dict[str, list[dict[str, Any]]] = {}
        for c in picked:
            by_traj.setdefault(c["traj_id"], []).append(c)

        # 刀2 · traj 内 dense 重排扩展:命中轨迹再拉同轨迹语义最相关的 states,
        # 修"检回正确轨迹、错误片段"(逐题对齐:88% unknown 题答案段不在窗口)
        if self._per_traj_extra > 0:
            expanded: dict[str, list[dict[str, Any]]] = {}
            for traj_id, chunks in by_traj.items():
                picked_ids = {id(c) for c in chunks}
                traj_chunk_idx = [
                    i for i, c in enumerate(self._chunks) if c["traj_id"] == traj_id
                ]
                scored = sorted(traj_chunk_idx, key=lambda i: -dense[i])
                extra = [
                    self._chunks[i]
                    for i in scored
                    if id(self._chunks[i]) not in picked_ids
                ]
                expanded[traj_id] = chunks + extra[: self._per_traj_extra]
            by_traj = expanded

        items: list[MemoryContextItem] = []
        used = 0
        shots: list[str] = []
        for traj_id, chunks in by_traj.items():
            meta = self._trajs.get(traj_id, {})
            header = f"[trajectory {traj_id} · env={meta.get('environment','')} · goal={meta.get('goal','')} · outcome={meta.get('outcome','')}]"
            body = "\n".join(
                f"state {c['state_idx']}: {c['text']}" for c in sorted(chunks, key=lambda c: c["state_idx"])
            )
            block = f"{header}\n{body}"
            if used + len(block) > self._text_budget and items:
                break
            items.append({"type": "text", "value": block})
            used += len(block)
            for c in sorted(chunks, key=lambda c: -fused[self._chunks.index(c)]):
                shot = c.get("screenshot")
                if shot and shot not in shots and len(shots) < self._max_screenshots:
                    shots.append(shot)
        for shot in shots:
            p = Path(shot)
            if p.exists():
                items.append({"type": "image", "value": str(p)})
        return items

    # ------------------------------------------------------------ persistence
    def _save_backend(self, output_dir: Path) -> None:
        import json

        payload = {
            "trajs": self._trajs,
            "chunks": self._chunks,
            "corpus": self._bm25_corpus,
        }
        (output_dir / "compass_index.json").write_text(
            json.dumps(payload, ensure_ascii=True), encoding="utf-8"
        )
        if self._matrix is not None:
            np.save(output_dir / "compass_matrix.npy", self._matrix)

    def _load_backend(self, input_dir: Path) -> None:
        import json

        data = json.loads(
            (input_dir / "compass_index.json").read_text(encoding="utf-8")
        )
        self._trajs = data["trajs"]
        self._chunks = data["chunks"]
        self._bm25_corpus = data["corpus"]
        mat_path = input_dir / "compass_matrix.npy"
        if mat_path.exists():
            self._matrix = np.load(mat_path)
        else:
            self._matrix = None
