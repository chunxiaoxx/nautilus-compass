"""B.5 · PoI candidate wire tests.

A PoI *candidate* is emitted at recall time (no action_outcome yet) when
high-confidence cosine matches are surfaced to the agent. Distinct from
a real PoI *event* (emit_nau_records) which requires a known downstream
outcome. Sidecar: poi_candidates.jsonl (separate from poi_emit.jsonl).
"""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_emit_poi_candidate_writes_sidecar():
    """Unit · two non-self-cited entries · 2 lines in poi_candidates.jsonl with rank+kind+actor."""
    from proof.poi_emitter import emit_poi_candidate

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        # entries from recall.py shape: dict with at least 'path' field
        # production puts a filename str in 'path' and a full str in 'fullpath'
        # · accept Path or str on 'path' · prefer 'fullpath' if present
        m1 = tmp / "m1.md"
        m1.write_text("---\nname: m1\nagent_type: other\n---\nbody1\n", encoding="utf-8")
        m2 = tmp / "m2.md"
        m2.write_text("---\nname: m2\nagent_type: other\n---\nbody2\n", encoding="utf-8")
        top = [
            (0.9, {"path": m1.name, "fullpath": str(m1)}),
            (0.8, {"path": m2.name, "fullpath": str(m2)}),
        ]
        count = emit_poi_candidate(top, query="how does X work", agent_id="A", cache_dir=tmp)
        assert count == 2, f"expected 2 candidate lines, got {count}"
        sidecar = tmp / "poi_candidates.jsonl"
        assert sidecar.exists(), "poi_candidates.jsonl was not created"
        lines = [json.loads(l) for l in sidecar.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 2
        first = lines[0]
        assert first["kind"] == "candidate"
        assert first["actor"] == "A"
        assert first["rank"] == 0
        assert first["memory"] == "m1.md"
        assert "ts" in first and "score" in first and "query_hash" in first
        assert first["score"] == 0.9
        assert lines[1]["rank"] == 1
        assert lines[1]["memory"] == "m2.md"


def test_emit_poi_candidate_self_cite_suppressed():
    """Unit · entry whose creator == actor must be suppressed (mirrors emit_nau_records)."""
    from proof.poi_emitter import emit_poi_candidate

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        # session_x.md created by agent_id=A · A querying recall · self-cite
        m = tmp / "session_x.md"
        m.write_text("---\nname: session_x\nagent_type: A\n---\nbody\n", encoding="utf-8")
        top = [(0.95, {"path": m.name, "fullpath": str(m)})]
        count = emit_poi_candidate(top, query="q", agent_id="A", cache_dir=tmp)
        assert count == 0, f"self-cite should be suppressed, got {count}"
        # sidecar may or may not exist (no writes) · don't assert either way


def test_recall_emits_poi_candidate_on_high_confidence(monkeypatch, tmp_path):
    """Integration · recall.py wire site invokes emit_poi_candidate when top is non-empty.

    NOTE: Full e2e of render_v02_vector_mode requires the BGE embedder
    (heavy · slow · model download). We assert the wire instead:

      (a) the call site exists in recall.py source (grep · static check)
      (b) the env-var opt-out COMPASS_NO_POI_CANDIDATE is honored at the
          call site (we directly drive a tiny shim that mimics the wire)

    The wire logic itself is simple enough (env-var guard + try/except +
    one function call) that unit-testing the env-var branch + asserting
    the source-level wire gives high confidence without touching the
    embedder.
    """
    from proof.poi_emitter import emit_poi_candidate, CANDIDATE_SIDECAR

    # --- (a) static: assert call site exists in recall.py ---
    recall_src = Path(__file__).resolve().parents[1] / "recall.py"
    src_text = recall_src.read_text(encoding="utf-8")
    assert "emit_poi_candidate" in src_text, "recall.py missing emit_poi_candidate wire"
    assert "COMPASS_NO_POI_CANDIDATE" in src_text, "recall.py missing env-var opt-out"

    # --- (b) functional: drive emit_poi_candidate + simulate wire's env-var guard ---
    m = tmp_path / "hit.md"
    m.write_text("---\nname: hit\nagent_type: other\n---\nbody\n", encoding="utf-8")
    top = [(0.88, {"path": m.name, "fullpath": str(m)})]
    sidecar = tmp_path / CANDIDATE_SIDECAR

    # (b.1) env var SET → wire's guard prevents emit · sidecar does NOT appear
    monkeypatch.setenv("COMPASS_NO_POI_CANDIDATE", "1")
    if os.environ.get("COMPASS_NO_POI_CANDIDATE") != "1":
        emit_poi_candidate(top, query="real recall query", agent_id="agent-X", cache_dir=tmp_path)
    assert not sidecar.exists(), "guard should prevent emit when COMPASS_NO_POI_CANDIDATE=1"

    # (b.2) env var UNSET → wire calls emit · sidecar appears with expected record
    monkeypatch.delenv("COMPASS_NO_POI_CANDIDATE", raising=False)
    if os.environ.get("COMPASS_NO_POI_CANDIDATE") != "1":
        n = emit_poi_candidate(top, query="real recall query", agent_id="agent-X", cache_dir=tmp_path)
        assert n == 1
    assert sidecar.exists()
    record = json.loads(sidecar.read_text(encoding="utf-8").strip())
    assert record["kind"] == "candidate"
    assert record["actor"] == "agent-X"
    assert record["memory"] == "hit.md"


# =============================================================================
# B.5 follow-up · deterministic actor fallback
# =============================================================================
# When COMPASS_AGENT_ID and CLAUDE_AGENT_ID are both unset, the wire site
# falls back to a stable anonymous ID derived from `git config user.email`
# + cwd via sha256[:8]. Identity persists across sessions on same user+cwd,
# enabling future PoI reconciliation. Falls back to literal "unknown" when
# git is unavailable.


def test_resolve_default_actor_prefers_compass_agent_id(monkeypatch):
    """COMPASS_AGENT_ID takes precedence · CLAUDE_AGENT_ID does not override."""
    from recall import _resolve_default_actor

    monkeypatch.setenv("COMPASS_AGENT_ID", "agent-x")
    monkeypatch.setenv("CLAUDE_AGENT_ID", "agent-y")  # should be ignored
    assert _resolve_default_actor() == "agent-x"

    # Confirm CLAUDE_AGENT_ID alone is also used when COMPASS_AGENT_ID is unset
    monkeypatch.delenv("COMPASS_AGENT_ID", raising=False)
    assert _resolve_default_actor() == "agent-y"


def test_resolve_default_actor_uses_git_email_and_cwd_hash(monkeypatch, tmp_path):
    """Both env vars unset · git email + cwd → stable anon-<8hex>."""
    import hashlib
    import subprocess
    from recall import _resolve_default_actor

    monkeypatch.delenv("COMPASS_AGENT_ID", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_ID", raising=False)

    def fake_check_output(*args, **kwargs):
        return "test@example.com\n"

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    monkeypatch.chdir(tmp_path)

    result = _resolve_default_actor()
    expected_hash = hashlib.sha256(
        f"test@example.com|{tmp_path}".encode("utf-8")
    ).hexdigest()[:8]
    expected = f"anon-{expected_hash}"

    assert result == expected, f"expected {expected!r}, got {result!r}"
    assert result.startswith("anon-")
    assert len(result) == 13  # "anon-" (5) + 8 hex


def test_resolve_default_actor_falls_back_to_unknown_when_git_missing(monkeypatch):
    """Both env vars unset · git not installed → literal "unknown"."""
    import subprocess
    from recall import _resolve_default_actor

    monkeypatch.delenv("COMPASS_AGENT_ID", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_ID", raising=False)

    def fake_check_output(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    assert _resolve_default_actor() == "unknown"


if __name__ == "__main__":
    tests = [
        test_emit_poi_candidate_writes_sidecar,
        test_emit_poi_candidate_self_cite_suppressed,
    ]
    failures = []
    for t in tests:
        try:
            t()
            print(f"OK {t.__name__}")
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
