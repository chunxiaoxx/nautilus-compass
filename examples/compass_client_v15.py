"""Compass Python client v1.5 · async HTTP wrapper for V5 / V6 / Kairos integration.

Drop-in replacement for `nautilus_v5/integrations/compass_client.py`. The existing
`compass_drift_prehook` function is preserved for backward compat (a thin alias to
the new `acompass_drift_check`). Three new functions close the loop:

  · acompass_recall       · GET  /v1/v14/recall  · top-k semantic memory
  · acompass_drift_check  · POST /v1/drift_check · BGE-m3 + anchors gate
  · acompass_ingest_obs   · POST /v1/observations · write outcome to compass
  · acompass_thread_recall (optional · for V7 multi-day threads · GET /v1/v14/thread_recall)

Closes the gap diagnosed by V7 at 2026-05-11 09:09: "compass_client.py 没有 recall
+ ingest_obs function · 只有 drift_prehook"。Now you have all three.

Wire pattern (V5/V6/Kairos cycle · 3-4 lines real diff):

```python
from compass_client_v15 import (
    acompass_recall, acompass_drift_check, acompass_ingest_obs,
)

async def v5_cycle(task):
    # 1 · recall · 拿前案
    recall = await acompass_recall(task.description, top_k=3)

    # 2 · 把 top3 注入 LLM prompt
    task.prompt_context = recall.format_for_llm()

    # 3 · drift_check (已有 · 别忘了真 gate 而不是软吞)
    drift = await acompass_drift_check(prompt=task.proposed_action)
    if drift.should_alert:
        await telegram_approve_gate(drift)
        return

    # 4 · action
    result = await do_action(task)

    # 5 · ingest_obs · 带 cited_snippets · self-reported proof_of_recall
    await acompass_ingest_obs(
        name=f"v5-cycle-{task.id}",
        body=result.summary,
        cited_snippets=recall.suggested_cites(),
        recall_id=recall.recall_id,
    )
```

Env vars:
  COMPASS_BASE_URL    = http://127.0.0.1:8770   (default)
  COMPASS_AGENT_TYPE  = nautilus-prime-001       (per-agent · sets X-Tenant-ID)
  COMPASS_TIMEOUT_S   = 8.0                      (per-call timeout)

Failure modes (all soft · never raise · agent must continue):
  · daemon unreachable    → returns empty Recall / soft DriftCheck / False ingest
  · BGE cold start (>8s)  → same
  · auth fail (401)       → log warning · return empty
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx  # already in V5 env per requirements.txt


log = logging.getLogger("compass_client_v15")

BASE_URL = os.environ.get("COMPASS_BASE_URL", "http://127.0.0.1:8770")
AGENT_TYPE = os.environ.get("COMPASS_AGENT_TYPE", "unknown")
TIMEOUT_S = float(os.environ.get("COMPASS_TIMEOUT_S", "20.0"))  # BGE cold-load needs 15-20s


# ─── data classes ──────────────────────────────────────────────────


@dataclass
class RecallHit:
    score: float
    path: str
    description: str
    project: str = ""
    age_str: str = ""


@dataclass
class Recall:
    """Result of acompass_recall · also tracks recall_id for proof-of-recall."""
    recall_id: str
    query: str
    hits: list[RecallHit] = field(default_factory=list)
    backend: str = "v1.4-bge-m3"
    issued_at: float = field(default_factory=time.time)

    def format_for_llm(self, n: int = 3) -> str:
        """Render top-n as compact text block · drop in to LLM prompt."""
        if not self.hits:
            return f"[compass.recall · 0 hits for {self.query!r}]"
        lines = [f"[compass.recall · top {min(n, len(self.hits))} for {self.query!r}]"]
        for h in self.hits[:n]:
            lines.append(f"  · {h.path} (score={h.score:.2f}) · {h.description[:120]}")
        return "\n".join(lines)

    def suggested_cites(self, n: int = 1) -> list[str]:
        """Pick path basenames for ingest_obs cited_snippets."""
        return [h.path.rsplit("/", 1)[-1] for h in self.hits[:n]]


@dataclass
class DriftCheck:
    score: float
    alignment: float
    deviation: float
    should_alert: bool
    top_neg_hits: list[dict] = field(default_factory=list)
    backend: str = ""
    note: str = ""


# ─── HTTP helpers ──────────────────────────────────────────────────


def _headers(extra: Optional[dict] = None, path: str = "") -> dict[str, str]:
    """X-Tenant-ID works for drift_check + v14 routes · /v1/observations needs X-User-ID.

    Send both to maximize compatibility · v0.9 drift_check picks Tenant first,
    /v1/observations picks X-User-ID (via Depends(auth_user)).
    """
    h = {
        "X-Tenant-ID": AGENT_TYPE,
        "X-User-ID": AGENT_TYPE,  # v0.9 /v1/observations uses this
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


async def _get(path: str, params: dict) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as cl:
            r = await cl.get(f"{BASE_URL}{path}", params=params, headers=_headers())
            if r.status_code != 200:
                log.warning(f"compass GET {path} → {r.status_code}: {r.text[:200]}")
                return None
            return r.json()
    except Exception as e:
        log.warning(f"compass GET {path} fail (soft): {type(e).__name__}: {e}")
        return None


async def _post(path: str, body: dict) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as cl:
            r = await cl.post(f"{BASE_URL}{path}", json=body, headers=_headers())
            if r.status_code not in (200, 201):
                log.warning(f"compass POST {path} → {r.status_code}: {r.text[:200]}")
                return None
            return r.json()
    except Exception as e:
        log.warning(f"compass POST {path} fail (soft): {type(e).__name__}: {e}")
        return None


# ─── public async API ─────────────────────────────────────────────


async def acompass_recall(query: str, top_k: int = 3, scope: str = "user",
                          project: Optional[str] = None) -> Recall:
    """Semantic recall against compass memory · returns top-k by BGE-m3 cosine.

    Default scope="user" · unions across all projects of this user (cross-project).
    Use scope="project" if you only want the current project's memory.

    Soft-fail safe: empty Recall on daemon down / 401 / cold start timeout.
    Always returns a Recall object so agent code doesn't need try/except.
    """
    recall_id = "rcl_" + uuid.uuid4().hex[:12]
    params: dict[str, Any] = {"q": query[:2000], "top_k": top_k, "scope": scope}
    if project:
        params["project"] = project

    data = await _get("/v1/v14/recall", params)
    if not data or not data.get("ok"):
        return Recall(recall_id=recall_id, query=query)

    hits = []
    for h in data.get("hits", []):
        hits.append(RecallHit(
            score=float(h.get("score", 0)),
            path=h.get("path", ""),
            description=h.get("description", "")[:300],
            project=h.get("project", ""),
            age_str=h.get("age_str", ""),
        ))
    return Recall(recall_id=recall_id, query=query, hits=hits,
                  backend=data.get("backend", "v1.4-bge-m3"))


async def acompass_drift_check(prompt: str) -> DriftCheck:
    """Run prompt against the platform_base + per-agent anchor pack.

    Returns DriftCheck with should_alert · agent SHOULD respect this gate.
    Soft-swallow (returning all-zero DriftCheck) only on transport error · not on alert.
    """
    if not prompt or len(prompt.strip()) < 5:
        return DriftCheck(score=0, alignment=1, deviation=0, should_alert=False, note="prompt too short")

    data = await _post("/v1/drift_check", {"prompt": prompt[:2000]})
    if not data:
        return DriftCheck(score=0, alignment=1, deviation=0, should_alert=False, note="compass unreachable")

    return DriftCheck(
        score=float(data.get("score", 0)),
        alignment=float(data.get("alignment", 1)),
        deviation=float(data.get("deviation", 0)),
        should_alert=bool(data.get("should_alert", False)),
        top_neg_hits=data.get("top_neg_hits", []),
        backend=data.get("backend", ""),
        note=data.get("note", ""),
    )


async def acompass_ingest_obs(
    name: str,
    body: str,
    drift: str = "green",
    type_: str = "discovery",
    cited_snippets: Optional[list[str]] = None,
    recall_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    thread_role: Optional[str] = None,
) -> bool:
    """Write an observation to compass · self-reported proof_of_recall.

    cited_snippets + recall_id together compose a soft proof-of-recall claim.
    Server-side validation may come in v1.6 · for now it's recorded as-is.

    Returns True if compass accepted the write · False on transport / auth fail.
    """
    if not name:
        log.warning("acompass_ingest_obs: name required")
        return False

    # v1.5 · use /v1/v14/ingest_obs · writes session_*.md to compass memory
    # (NOT v0.9 /v1/observations · which is the old SaaS SQLite path)
    payload: dict[str, Any] = {
        "name": name[:80],
        "content": (body or "")[:8000],
        "description": (body or "")[:200],
        "drift": drift if drift in ("green", "yellow", "red") else "green",
    }
    if cited_snippets:
        payload["cited_snippets"] = cited_snippets
    if recall_id:
        payload["recall_id"] = recall_id
    if thread_id:
        payload["thread_id"] = thread_id
    if thread_role:
        payload["thread_role"] = thread_role

    data = await _post("/v1/v14/ingest_obs", payload)
    if not data or not data.get("ok"):
        return False
    log.info(f"compass.ingest_obs · {data.get('session_name','?')} · proof={data.get('proof_of_recall','?')}")
    return True


async def acompass_thread_recall(thread_id: str, limit: int = 50) -> list[dict]:
    """v1.1 · Return chronological message stream for a thread_id.

    Use for V7 partnership-loop multi-day negotiations · for any cron that
    iterates a long conversation. Returns [] on miss / transport fail.
    """
    if not thread_id:
        return []
    data = await _get("/v1/v14/thread_recall", {"thread_id": thread_id, "limit": limit})
    if not data or not data.get("ok"):
        return []
    return data.get("hits", [])


# ─── backward-compat shim · existing V5/V6/Kairos code ─────────────


async def acompass_drift_prehook(prompt: str) -> dict:
    """Legacy name · alias to acompass_drift_check · returns dict not dataclass.

    Old V5/V6/Kairos callers use:
        score = (await acompass_drift_prehook(prompt))["score"]

    Don't change those · just import this from compass_client_v15 instead of
    the old compass_client. Behavior identical.
    """
    dc = await acompass_drift_check(prompt)
    return {
        "score": dc.score,
        "alignment": dc.alignment,
        "deviation": dc.deviation,
        "should_alert": dc.should_alert,
        "top_neg_hits": dc.top_neg_hits,
        "backend": dc.backend,
        "note": dc.note,
    }


# Sync wrapper for non-async callsites
def compass_drift_prehook(prompt: str) -> dict:
    """Sync alias · spins event loop · for legacy non-async V5 paths."""
    return asyncio.get_event_loop().run_until_complete(acompass_drift_prehook(prompt))


# ─── self-test (run as script · uses real compass at COMPASS_BASE_URL) ─────


async def _smoke() -> int:
    print(f"compass_client_v15 · BASE={BASE_URL} · agent={AGENT_TYPE}")
    print()

    # 1 · drift_check
    dc = await acompass_drift_check("test prompt for compass smoke v1.5 client")
    print(f"drift_check · should_alert={dc.should_alert} · backend={dc.backend}")
    print(f"  score={dc.score} alignment={dc.alignment}")
    print()

    # 2 · recall
    r = await acompass_recall("fake closure 305 P1-1", top_k=3)
    print(f"recall · recall_id={r.recall_id} · {len(r.hits)} hits · backend={r.backend}")
    for h in r.hits[:3]:
        print(f"  · score={h.score:.3f} · {h.path}")
    print()
    print("format_for_llm preview:")
    print(r.format_for_llm())
    print()

    # 3 · ingest_obs (with self-reported proof)
    ok = await acompass_ingest_obs(
        name="compass_client_v15 smoke",
        body="Verifying the v1.5 client lib end-to-end against cloud compass.",
        cited_snippets=r.suggested_cites(),
        recall_id=r.recall_id,
    )
    print(f"ingest_obs · ok={ok}")

    return 0 if dc.backend or r.hits else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    sys.exit(asyncio.run(_smoke()))
