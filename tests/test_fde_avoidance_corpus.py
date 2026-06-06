"""Task A1 · batch avoidance-corpus build driver (W6 substrate).

`ops/fde_avoidance_corpus_build` is the glue that turns all the real FDE
verdict+checklist pairs into recallable per-dimension avoid-pitfall / proven
knowledge atoms (the W6 substrate v5's copilot recalls before solving the next
task). The driver owns two seams:

  · load_fde_tasks — discover {task_id, checklist, verdict} from the on-disk
    `_v5_<uid>_real_verdict_<date>.json` + `<uid>_checklist.json` files, picking
    the LATEST verdict per task (a rescored verdict supersedes its predecessor),
    UTF-8 (the files are CJK — gbk default would crash on Windows).
  · build_corpus — wire the (injected) vtf capsule callables into the existing
    proof.fde_batch_ingest pipeline so atoms accumulate + dimensions get PoI.

The vtf atom FORMAT (避坑/亮点 marker) is tested by vtf's own suite; here we test
the DRIVER contract (loading + wiring) with stubs so CI stays compass-only. NO LLM.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
from ops import fde_avoidance_corpus_build as drv  # noqa: E402

NOW = "2026-06-06T12:00:00Z"


def _write(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def _verdict(task_uid, items, score=1.0):
    return {"task_uid": task_uid, "score": score, "passed": sum(1 for i in items if i["pass"]),
            "total": len(items), "veto_failed": False,
            "overall_pass": all(i["pass"] for i in items), "items": items}


def _checklist(task_uid, items):
    return {"task_uid": task_uid, "items": items}


def _mk_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


# ── RED 1 · loader picks the LATEST verdict per task ─────────────────────────
def test_load_picks_latest_verdict_per_task(tmp_path):
    vdir = tmp_path / "v"; cdir = tmp_path / "c"
    vdir.mkdir(); cdir.mkdir()
    # data_003 has two verdicts: an older one and a rescored newer one
    _write(vdir / "_v5_data003_real_verdict_20260605.json",
           _verdict("data_003", [{"id": "c1", "pass": False, "reason": "old"}], score=0.3))
    _write(vdir / "_v5_data003_real_verdict_20260606.json",
           _verdict("data_003", [{"id": "c1", "pass": True, "reason": "rescored"}], score=0.9))
    _write(cdir / "data_003_checklist.json",
           _checklist("data_003", [{"id": "c1", "point": "p", "dimension": "calc-formula"}]))

    tasks = drv.load_fde_tasks(str(vdir), str(cdir))

    assert len(tasks) == 1
    t = tasks[0]
    assert t["task_id"] == "data_003"
    # the rescored (20260606) verdict wins
    assert t["verdict"]["score"] == 0.9
    assert t["verdict"]["items"][0]["reason"] == "rescored"


# ── RED 2 · loader reads UTF-8 CJK + joins checklist by task_uid ──────────────
def test_load_reads_utf8_and_joins_checklist(tmp_path):
    vdir = tmp_path / "v"; cdir = tmp_path / "c"
    vdir.mkdir(); cdir.mkdir()
    _write(vdir / "_v5_data002_real_verdict_20260605.json",
           _verdict("data_002", [{"id": "c4", "pass": False, "reason": "隐私红线被突破·避坑"}]))
    _write(cdir / "data_002_checklist.json",
           _checklist("data_002", [{"id": "c4", "point": "匿名化处理", "dimension": "task-specific"}]))

    tasks = drv.load_fde_tasks(str(vdir), str(cdir))

    assert tasks[0]["task_id"] == "data_002"
    assert tasks[0]["verdict"]["items"][0]["reason"] == "隐私红线被突破·避坑"
    assert tasks[0]["checklist"]["items"][0]["point"] == "匿名化处理"


# ── RED 3 · a verdict with no matching checklist is skipped (warned) ─────────
def test_load_skips_task_without_checklist(tmp_path):
    vdir = tmp_path / "v"; cdir = tmp_path / "c"
    vdir.mkdir(); cdir.mkdir()
    _write(vdir / "_v5_data009_real_verdict_20260605.json",
           _verdict("data_009", [{"id": "c1", "pass": True, "reason": "ok"}]))
    # no data_009_checklist.json

    tasks = drv.load_fde_tasks(str(vdir), str(cdir))
    assert tasks == []


# ── RED 3b · task_uid absent in verdict → derive from filename token ─────────
# (real data: data_001's verdict carries answer_len, not task_uid; the filename
# token `data001` must normalize to the canonical `data_001` checklist key)
def test_load_derives_task_uid_from_filename_when_absent(tmp_path):
    vdir = tmp_path / "v"; cdir = tmp_path / "c"
    vdir.mkdir(); cdir.mkdir()
    v = _verdict("data_001", [{"id": "c1", "pass": True, "reason": "ok"}])
    del v["task_uid"]  # mimic data_001's real shape (no task_uid)
    _write(vdir / "_v5_data001_real_verdict_20260605.json", v)
    _write(cdir / "data_001_checklist.json",
           _checklist("data_001", [{"id": "c1", "point": "p", "dimension": "coverage"}]))

    tasks = drv.load_fde_tasks(str(vdir), str(cdir))
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "data_001"


# ── RED 4 · build_corpus feeds each task through atoms + credits dimensions ──
def test_build_corpus_feeds_each_task_and_credits_dimensions(tmp_path):
    conn = _mk_db()
    mem_dir = str(tmp_path / "mem")

    tasks = [
        {"task_id": "data_001",
         "checklist": _checklist("data_001", [
             {"id": "c1", "point": "用公式测算", "dimension": "calc-formula"},
             {"id": "c4", "point": "匿名化", "dimension": "hallucination-control"}]),
         "verdict": _verdict("data_001", [
             {"id": "c1", "pass": True, "reason": "公式正确"},
             {"id": "c4", "pass": False, "reason": "泄露隐私·避坑"}], score=0.9)},
    ]

    seen_build = []
    seen_ingest = []

    def stub_build(task_id, checklist, verdict):
        seen_build.append(task_id)
        # mimic vtf: one atom per scored item, fail → avoidance
        return [{"dimension": it["dimension"], "checklist_id": it["id"],
                 "passed": vi["pass"], "knowledge": vi["reason"]}
                for it, vi in zip(checklist["items"], verdict["items"])]

    def stub_ingest(atoms, md):
        seen_ingest.append(atoms)
        return {a["dimension"]: f"{md}/fde-dim-{a['dimension']}.md" for a in atoms}

    def stub_dim(item):
        return item["dimension"]

    res = drv.build_corpus(tasks, mem_dir, conn, NOW, build_atoms=stub_build,
                           ingest_atoms=stub_ingest, dimension_for=stub_dim,
                           placeholder="?")

    # each task fed through both vtf seams
    assert seen_build == ["data_001"]
    assert len(seen_ingest) == 1
    # the failed item (c4) IS present in the atoms handed to ingest (avoidance kept)
    fail_atoms = [a for batch in seen_ingest for a in batch if not a["passed"]]
    assert any(a["checklist_id"] == "c4" for a in fail_atoms)
    # passed dimension credited; failed dimension NOT credited (0, only capsule kept)
    from proof import fde_poi_adapter as adp

    def dim_credit(dim):
        return conn.execute("SELECT cumulative_impact FROM poi_credit WHERE memory_key=?",
                            (adp.dimension_memory_key(dim),)).fetchone()

    assert dim_credit("calc-formula") is not None
    assert dim_credit("hallucination-control") is None
    # result surfaces accumulated atom paths
    assert "calc-formula" in res["atom_paths"]
