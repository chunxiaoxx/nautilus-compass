import json
from pathlib import Path
from proof.poi_emitter import emit_poi_candidate

def test_candidate_carries_project_and_creator(tmp_path):
    mem = tmp_path / "projects" / "C--Users-chunx" / "memory" / "m.md"
    mem.parent.mkdir(parents=True)
    mem.write_text("---\nagent_type: other-agent\n---\nbody", encoding="utf-8")
    top = [(0.9, {"fullpath": str(mem), "path": "m.md"})]
    n = emit_poi_candidate(top, query="q", agent_id="me", cache_dir=tmp_path)
    line = json.loads((tmp_path / "poi_candidates.jsonl").read_text().splitlines()[0])
    assert n == 1
    assert line["project"] == "C--Users-chunx"
    assert line["memory"] == "m.md"
    assert line["creator"] == "other-agent"
