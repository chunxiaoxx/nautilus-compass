"""CS-018 UT:末笔全量入账判定(passrate 全对率口径)。

四组用例必须全过才算 1.0,任一失败为 0。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from ledger_stream import ingest_daily, parse_stream  # noqa: E402


def _mk(tmp_path, rows, trailing_newline):
    body = "".join(json.dumps(r) + "\n" for r in rows[:-1])
    body += json.dumps(rows[-1]) + ("\n" if trailing_newline else "")
    p = tmp_path / "stream.jsonl"
    p.write_text(body, encoding="utf-8")
    return p


def test_ut1_tail_no_newline_full_ingest(tmp_path):
    """UT1[主判定] 末行无换行符:全量入账,末笔不丢。"""
    rows = [{"tx": f"T{i:04d}", "amount": 100 + i} for i in range(10000)]
    p = _mk(tmp_path, rows, trailing_newline=False)
    st = ingest_daily(p)
    assert st.tx_count == 10000, f"丢笔:{st.tx_count}/10000"
    assert st.sum_amount == sum(r["amount"] for r in rows)


def test_ut2_tail_with_newline_still_full(tmp_path):
    """UT2[回归] 末行带换行符:不受修复影响,仍全量。"""
    rows = [{"tx": f"T{i:04d}", "amount": 200 + i} for i in range(50)]
    p = _mk(tmp_path, rows, trailing_newline=True)
    st = ingest_daily(p)
    assert st.tx_count == 50
    assert st.sum_amount == sum(r["amount"] for r in rows)


def test_ut3_single_line_no_newline(tmp_path):
    """UT3[边界] 仅一笔且无换行:一笔入账。"""
    p = _mk(tmp_path, [{"tx": "T0001", "amount": 999}], trailing_newline=False)
    st = ingest_daily(p)
    assert st.tx_count == 1 and st.sum_amount == 999


def test_ut4_parse_stream_returns_all_rows(tmp_path):
    """UT4[口径] parse_stream 与 ingest_daily 笔数一致(§3 全量语义)。"""
    rows = [{"tx": f"T{i:04d}", "amount": 1} for i in range(7)]
    p = _mk(tmp_path, rows, trailing_newline=False)
    assert len(parse_stream(p)) == 7 == ingest_daily(p).tx_count
