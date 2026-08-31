"""verdict-hook 测试:run verdict 自动提炼进燃料 pending 池(双环回流)。"""
import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import verdict_hook as vh


@pytest.fixture
def roots(tmp_path, monkeypatch):
    scan = tmp_path / "vtf" / "_compass_lmev2_out" / "d12" / "compass_web_small"
    scan.mkdir(parents=True)
    pool = tmp_path / "vtf" / "fuel_pool"
    monkeypatch.setattr(vh, "REPO", tmp_path)
    monkeypatch.setattr(vh, "SCAN_ROOTS", [tmp_path / "vtf"])
    monkeypatch.setattr(vh, "PENDING", pool / "pending")
    monkeypatch.setattr(vh, "LOG", pool / "intake_log.jsonl")
    monkeypatch.setattr(vh, "CURSOR", pool / "verdict_cursor.json")
    return scan, pool


AGG = {
    "overall": {
        "overall_full_set": 0.367,
        "overall_non_abstention_only": 0.327,
        "overall_abstention_only": 0.458,
        "count_all_questions": 240,
    },
    "non_abstention_by_category": {
        "procedure": {"count": 42, "pct_correct": 0.690},
        "static": {"count": 60, "pct_correct": 0.183},
    },
}


def test_extract_from_aggregated(roots):
    scan, _ = roots
    (scan / "aggregated_metrics.json").write_text(json.dumps(AGG), encoding="utf-8")
    items = vh.extract_from_run(scan)
    assert len(items) == 1
    body = items[0]
    assert "36.7%" in body and "240" in body
    assert "procedure" in body and "69.0%" in body  # 强分类
    assert "static" in body and "18.3%" in body  # 弱分类


def test_extract_from_md_verdict_paragraph(roots):
    scan, _ = roots
    md = scan / "verdict_note.md"
    md.write_text(
        "背景介绍无关内容很短。\n\n"
        "d13 web 域判定 NEGATIVE:刀3 LoRA 检索器 web 域 0.283 vs d12 0.367,"
        "预期 +8-12pt 落空,预注册判据未通过,退回 d12 检索栈。\n\n"
        "另一段没有信号词的普通段落,讲的是会议纪要与日常安排,不构成裁决内容。\n",
        encoding="utf-8",
    )
    items = vh.extract_from_run(scan)
    assert len(items) == 1
    assert "NEGATIVE" in items[0] and "0.283" in items[0]


def test_no_signal_no_candidate(roots):
    scan, _ = roots
    (scan / "notes.md").write_text("纯会议纪要,没有任何裁决信号词的普通段落。" * 3, encoding="utf-8")
    (scan / "run_args.json").write_text(json.dumps({"model": "x"}), encoding="utf-8")
    assert vh.extract_from_run(scan) == []


def test_cursor_skips_unchanged(roots):
    scan, _ = roots
    (scan / "aggregated_metrics.json").write_text(json.dumps(AGG), encoding="utf-8")
    n1 = vh.run_hook()
    assert n1 == 1
    n2 = vh.run_hook()
    assert n2 == 0  # mtime 未变,游标跳过


def test_pending_entry_format(roots):
    scan, pool = roots
    (scan / "aggregated_metrics.json").write_text(json.dumps(AGG), encoding="utf-8")
    vh.run_hook()
    files = list((pool / "pending").glob("*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "status: pending_qc" in text
    assert "verdict_type: run-verdict" in text
    assert "source_verdict:" in text
    assert "qc_protocol: control-first-fail (Gate B)" in text
    # log 同步追加供 hash 去重
    assert (pool / "intake_log.jsonl").exists()


def test_real_d12_aggregated_yields_candidate(tmp_path, monkeypatch):
    """真数据冒烟:仓内 d12 真产物能出条目。"""
    real = Path(__file__).resolve().parents[1] / "vtf" / "_compass_lmev2_out" / "d12" / "compass_web_small"
    agg = real / "aggregated_metrics.json"
    if not agg.exists():
        pytest.skip("d12 产物不在")
    scan = tmp_path / "run"
    scan.mkdir()
    (scan / "aggregated_metrics.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8")
    items = vh.extract_from_run(scan)
    assert items and "·" in items[0]  # 模板化分隔符,非裸 json dump
