#!/usr/bin/env python3
"""compass · A 簇避坑语料语义检索(替裸 cat · RSI grounded-retrieval 热路径).

现状:`autolab_avoid_<task>.md`(autolab_corpus_ingest.py 产)被 producer round-2
grounded 臂裸 `cat` 整篇注入。corpus 一旦跨任务/多轮累积变厚,裸 cat 把无关原子也塞进
context → 稀释信号。本模块用 compass 现成 bge-m3 dense + bge-reranker-v2-m3(daemon
同模型·benchmark P@5 0.86→0.932)按 producer 的优化子目标 query 召回**最相关**避坑原子。

turf:compass=检索+语料 · V5=retrieve 调用+注入。embed/rerank 后端注入(默认懒加载真模型·
测试注 stub)→ CI 保持 compass-only 无模型无 LLM。

设计铁律:**批次平衡警示(correctness-first 元课)永远保留**,不受检索排序丢弃 —— 首验实证
naive grounding 推激进优化破坏正确性致 ΔReward 负,这条元课是 metamemory 质量门,无条件注入。

用法(V5 自助·drop-in 替 `cat corpus`):
  python3 autolab_corpus_retrieve.py --task radix_sort --query "访存带宽优化" [--top-k 3]
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys

CORPUS_DIR = os.environ.get("AUTOLAB_CORPUS_DIR", "/mnt/datadisk0/autolab_eval/corpus")

# 复用 daemon 同模型路径(本地 ModelScope 优先 · 否则 HF repo id)
_EMBEDDER_MODEL = os.environ.get("ZMM_EMBEDDER_MODEL", "BAAI/bge-m3")
_RERANKER_MODEL = os.environ.get("ZMM_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
_RERANK_CANDIDATES = int(os.environ.get("COMPASS_RERANK_CANDIDATES", "30"))

_ATOM_RE = re.compile(
    r"^- cand=(?P<cand>\S+)\s+reward=(?P<reward>[0-9.]+)"
    r"(?:\s+median=(?P<median>[0-9.]+)s?)?\s*\[(?P<tag>[^\]]+)\]:\s*(?P<text>.*)$"
)


def parse_corpus(md_text: str) -> dict:
    """Split the avoid-corpus markdown into {balance: [str], atoms: [dict]}.

    balance = the ⚠️ batch-warning lines (correctness-first meta-lesson · always
    kept). atoms = the `- cand=...` candidate-avoidance lines, each parsed to
    {cand, reward, median, tag, text, raw}.
    """
    balance: list = []
    atoms: list = []
    for line in md_text.splitlines():
        s = line.strip()
        if s.startswith("⚠️"):
            balance.append(s)
            continue
        m = _ATOM_RE.match(line.rstrip())
        if m:
            atoms.append({
                "cand": m.group("cand"),
                "reward": float(m.group("reward")),
                "median": float(m.group("median")) if m.group("median") else None,
                "tag": m.group("tag"),
                "text": m.group("text").strip(),
                "raw": line.rstrip(),
            })
    return {"balance": balance, "atoms": atoms}


def _cosine(a, b) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def retrieve(query, atoms, top_k=3, embed_fn=None, rerank_fn=None,
             candidates=_RERANK_CANDIDATES):
    """Rank avoid-atoms by relevance to `query`: bge-m3 dense → optional rerank.

    embed_fn(text)->vector dense-scores every atom (cosine vs query); the top
    `candidates` go to rerank_fn(query, [texts])->[scores] which decides the final
    order. rerank_fn=None → dense order. Returns the top_k atom dicts.
    """
    if not atoms:
        return []
    embed_fn = embed_fn or _default_embed_fn()
    qv = embed_fn(query)
    scored = [(_cosine(qv, embed_fn(a["text"])), a) for a in atoms]
    scored.sort(key=lambda x: -x[0])  # stable: ties keep corpus order
    short = [a for _s, a in scored[:candidates]]
    if rerank_fn is not None and short:
        rscores = rerank_fn(query, [a["text"] for a in short])
        short = [a for a, _s in sorted(zip(short, rscores), key=lambda x: -float(x[1]))]
    return short[:top_k]


def build_grounding(md_text, query, top_k=3, embed_fn=None, rerank_fn=None) -> str:
    """Drop-in replacement for `cat corpus`: the grounding text the producer's
    round-2 arm injects. = balance-warning (ALWAYS · highest priority) + the
    top_k query-relevant avoid-atoms. Subset, not wholesale dump.
    """
    parsed = parse_corpus(md_text)
    hits = retrieve(query, parsed["atoms"], top_k=top_k,
                    embed_fn=embed_fn, rerank_fn=rerank_fn)
    out = ["# 避坑(语义检索·按 query 召回 top-%d)" % top_k,
           "> query: %s" % query, ""]
    if parsed["balance"]:
        out.append("## 平衡警示(最高优先·无条件)")
        out.extend(parsed["balance"])
        out.append("")
    out.append("## 相关避坑原子")
    out.extend(h["raw"] for h in hits)
    return "\n".join(out) + "\n"


# ── default real-model backends (lazy · GPU bge-m3 + reranker) ───────────────
_EMBEDDER_SINGLETON = None
_RERANKER_SINGLETON = None


def _default_embed_fn():
    """Lazy bge-m3 SentenceTransformer encoder (daemon-equivalent). cuda autodetect."""
    global _EMBEDDER_SINGLETON
    if _EMBEDDER_SINGLETON is None:
        from sentence_transformers import SentenceTransformer
        try:
            import torch
            device = os.environ.get("ZMM_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        except Exception:
            device = os.environ.get("ZMM_DEVICE", "cpu")
        model = SentenceTransformer(_EMBEDDER_MODEL, device=device)
        _EMBEDDER_SINGLETON = lambda text: model.encode(text).tolist()  # noqa: E731
    return _EMBEDDER_SINGLETON


def _default_rerank_fn():
    """Lazy bge-reranker-v2-m3 CrossEncoder (daemon-equivalent)."""
    global _RERANKER_SINGLETON
    if _RERANKER_SINGLETON is None:
        from sentence_transformers import CrossEncoder
        try:
            import torch
            device = os.environ.get("ZMM_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        except Exception:
            device = os.environ.get("ZMM_DEVICE", "cpu")
        ce = CrossEncoder(_RERANKER_MODEL, device=device)
        _RERANKER_SINGLETON = lambda query, texts: [float(s) for s in ce.predict([(query, t) for t in texts])]  # noqa: E731
    return _RERANKER_SINGLETON


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--no-rerank", action="store_true",
                    help="dense only (skip cross-encoder · faster · no reranker model)")
    a = ap.parse_args()
    path = os.path.join(CORPUS_DIR, f"autolab_avoid_{a.task}.md")
    if not os.path.exists(path):
        print(f"[no corpus] {path}", file=sys.stderr); sys.exit(1)
    md = open(path, encoding="utf-8").read()
    rerank = None if a.no_rerank else _default_rerank_fn()
    print(build_grounding(md, a.query, top_k=a.top_k, rerank_fn=rerank))
