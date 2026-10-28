"""
P3 · Karpathy RAID-2 v2 fidelity_checker (5/22).

Computes fidelity_score 0.0-1.0 · how well executor output matches original task spec.
Uses compass V2 drift_check MCP tool.

Returns fidelity_score · used in raid_engine final consensus formula:
  final_score = quality_score × fidelity_score
  Both must ≥ 0.7 for consensus pass.

Stored in raid_votes.fidelity_score column (added by add_fidelity_score_raid_votes.sql).

Falls back to heuristic (Jaccard similarity of words) if compass MCP unavailable.
"""
from __future__ import annotations

import json
import logging
import os
import re
import socket
from typing import Optional

logger = logging.getLogger(__name__)

COMPASS_MCP_HOST = os.getenv("COMPASS_MCP_HOST", "127.0.0.1")
COMPASS_MCP_PORT = int(os.getenv("COMPASS_MCP_PORT", "9876"))
COMPASS_MCP_TIMEOUT = float(os.getenv("COMPASS_MCP_TIMEOUT", "1.5"))

FIDELITY_THRESHOLD = 0.7


def _compass_drift_check(prompt: str, project: str = "platform") -> Optional[dict]:
    """Call compass BGE daemon drift action · TCP JSON. Returns dict or None on failure."""
    if not prompt or not prompt.strip():
        return None
    try:
        request = {"action": "drift", "query": prompt.strip()[:2000], "project": project, "top_k": 1}
        with socket.create_connection((COMPASS_MCP_HOST, COMPASS_MCP_PORT), timeout=COMPASS_MCP_TIMEOUT) as sock:
            sock.settimeout(COMPASS_MCP_TIMEOUT)
            sock.sendall((json.dumps(request) + "\n").encode("utf-8"))
            buf = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
                if buf.endswith(b"\n"):
                    break
        resp = json.loads(buf.decode("utf-8"))
        if not resp.get("ok"):
            logger.info(f"compass drift not-ok: {resp.get('error')}")
            return None
        return resp.get("drift") or {}
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        logger.info(f"compass daemon unreachable: {e}")
        return None
    except Exception as e:
        logger.warning(f"compass drift failed: {e}")
        return None


def _heuristic_fidelity(spec: str, output: str) -> float:
    """Fallback when compass MCP unavailable · Jaccard similarity of significant words."""
    if not spec or not output:
        return 0.0

    def tokens(s: str) -> set:
        words = re.findall(r"[A-Za-z一-鿿]{3,}", s.lower())
        stop = {"the", "and", "for", "are", "with", "this", "that", "from", "have", "you", "your"}
        return set(w for w in words if w not in stop)

    spec_t = tokens(spec)
    out_t = tokens(output)
    if not spec_t:
        return 0.5

    intersection = len(spec_t & out_t)
    union = len(spec_t | out_t)
    if union == 0:
        return 0.0
    return round(intersection / union, 3)


def check_fidelity(task_spec: str, output: str) -> dict:
    """
    Compute fidelity_score for output vs task_spec.

    Returns dict with:
        - fidelity_score: 0.0-1.0
        - method: 'compass_drift' or 'heuristic'
        - passes_threshold: bool (≥ FIDELITY_THRESHOLD)
        - raw: compass output if available
    """
    drift = _compass_drift_check(f"Task: {task_spec[:500]}\n\nOutput: {output[:1500]}")

    if drift is not None:
        # compass returns drift score · we invert: low drift = high fidelity
        # Look for 'score' or 'drift' fields in various forms
        score = None
        if isinstance(drift, dict):
            for key in ("fidelity_score", "score", "similarity"):
                if key in drift and isinstance(drift[key], (int, float)):
                    score = float(drift[key])
                    break
            if score is None:
                for key in ("drift_score", "drift"):
                    if key in drift and isinstance(drift[key], (int, float)):
                        score = max(0.0, 1.0 - float(drift[key]))
                        break

        if score is not None:
            return {
                "fidelity_score": round(max(0.0, min(1.0, score)), 3),
                "method": "compass_drift",
                "passes_threshold": score >= FIDELITY_THRESHOLD,
                "raw": drift,
            }

    # Fallback
    heuristic = _heuristic_fidelity(task_spec, output)
    return {
        "fidelity_score": heuristic,
        "method": "heuristic",
        "passes_threshold": heuristic >= FIDELITY_THRESHOLD,
        "raw": None,
    }


def final_consensus_score(quality_score: float, fidelity_score: float) -> dict:
    """
    Karpathy v2 formula: final = quality × fidelity · both must ≥ 0.7 for pass.
    """
    q = float(quality_score or 0)
    f = float(fidelity_score or 0)
    final = round(q * f, 3)
    passes = q >= FIDELITY_THRESHOLD and f >= FIDELITY_THRESHOLD
    return {
        "quality_score": q,
        "fidelity_score": f,
        "final_score": final,
        "passes_consensus": passes,
        "fail_reason": (
            None if passes
            else f"quality={q} fidelity={f} threshold={FIDELITY_THRESHOLD}"
        ),
    }
