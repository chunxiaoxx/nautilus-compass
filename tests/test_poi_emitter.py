"""S4 module 3 · poi_emitter smoke tests."""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proof.poi_schema import ProofOfImpact
from proof.poi_emitter import (
    emit_nau_records, emit_event_log, update_frontmatter_cumulative, emit_full,
    NAU_SIDECAR, EVENT_LOG,
)


def _poi(score=0.5, cites=None, agent="acting-agent"):
    p = ProofOfImpact(
        action_id="b-test",
        agent_id=agent,
        cited_memory_paths=cites or ["m_1.md"],
        action_outcome="success",
        timestamp_action="2026-05-21T12:00:00Z",
        timestamp_outcome="2026-05-21T12:05:00Z",
    )
    p.impact_score = score
    return p


def _make_memory(tmp: Path, name: str, agent_type: str = "creator-agent") -> Path:
    p = tmp / name
    p.write_text(
        f"---\nname: {name}\nagent_type: {agent_type}\n---\nbody\n",
        encoding="utf-8",
    )
    return p


def test_1_emit_nau_records():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "m_1.md", agent_type="other-agent")
        poi = _poi(score=0.5, cites=[str(m)], agent="acting-agent")
        count = emit_nau_records(poi, cache_dir=tmp)
        assert count == 1
        sidecar = tmp / NAU_SIDECAR
        assert sidecar.exists()
        entry = json.loads(sidecar.read_text(encoding="utf-8").strip())
        assert entry["actor"] == "acting-agent"
        assert entry["creator"] == "other-agent"
    print("OK 1 NAU records emitted")


def test_2_self_cite_suppressed():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "self.md", agent_type="acting-agent")
        poi = _poi(cites=[str(m)], agent="acting-agent")
        count = emit_nau_records(poi, cache_dir=tmp)
        assert count == 0  # self-cite suppressed
    print("OK 2 self-cite suppressed")


def test_3_event_log_appended():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        poi = _poi(score=0.7, cites=["x.md"])
        log_path = emit_event_log(poi, cache_dir=tmp)
        assert log_path.exists()
        line = log_path.read_text(encoding="utf-8").strip()
        d = json.loads(line)
        assert d["action_id"] == "b-test"
        assert d["impact_score"] == 0.7
    print("OK 3 event log appended")


def test_4_frontmatter_update_new_fields():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "m.md")
        ok = update_frontmatter_cumulative(m, impact_delta=0.5)
        assert ok
        text = m.read_text(encoding="utf-8")
        assert "cumulative_impact: 0.5" in text
        assert "impact_event_count: 1" in text
        assert "last_impact_at:" in text
    print("OK 4 frontmatter new fields added")


def test_5_frontmatter_update_cumulative():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "m.md")
        update_frontmatter_cumulative(m, 0.3)
        update_frontmatter_cumulative(m, 0.5)
        text = m.read_text(encoding="utf-8")
        assert "cumulative_impact: 0.8" in text
        assert "impact_event_count: 2" in text
    print("OK 5 frontmatter cumulative correct")


def test_6_frontmatter_missing_file_returns_false():
    assert not update_frontmatter_cumulative(Path("/nonexistent/m.md"), 0.5)
    print("OK 6 missing file returns false")


def test_7_emit_full_orchestrates():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "m.md", agent_type="other")
        poi = _poi(score=0.6, cites=[str(m)], agent="acting")
        result = emit_full(poi, cache_dir=tmp)
        assert result["nau_records"] == 1
        assert result["frontmatter_updated"] == 1
        assert (tmp / EVENT_LOG).exists()
        assert (tmp / NAU_SIDECAR).exists()
    print("OK 7 emit_full orchestrates 3 sinks")


def test_8_negative_impact_emits():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "m.md", agent_type="other")
        poi = _poi(score=-0.3, cites=[str(m)], agent="acting")
        count = emit_nau_records(poi, cache_dir=tmp)
        assert count == 1  # negative still emitted (penalty signal)
        entry = json.loads((tmp / NAU_SIDECAR).read_text(encoding="utf-8").strip())
        assert entry["nau"] < 0
    print("OK 8 negative impact emits (penalty)")


if __name__ == "__main__":
    tests = [test_1_emit_nau_records, test_2_self_cite_suppressed,
             test_3_event_log_appended, test_4_frontmatter_update_new_fields,
             test_5_frontmatter_update_cumulative, test_6_frontmatter_missing_file_returns_false,
             test_7_emit_full_orchestrates, test_8_negative_impact_emits]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} poi_emitter smoke pass")
