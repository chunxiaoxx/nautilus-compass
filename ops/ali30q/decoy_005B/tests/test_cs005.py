# -*- coding: utf-8 -*-
"""CS-005B 判分 UT · 联审聚合层(audit_policy §4 切分合并贯穿 campaign)。8 UT / 3 gating。"""
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent / "environment" / "workspace" / "repo"
sys.path.insert(0, str(REPO))

from audit.campaign import campaign_audit


def _row(i, amount=1.0, weight=1, prefix="R"):
    return {"id": f"{prefix}{i}", "amount": amount, "weight": weight}


def _long(n, prefix, amount=1.0, weight=1):
    return [_row(i, amount=amount, weight=weight, prefix=prefix) for i in range(n)]


# ─── gating 3 ───
def test_short_shard_exposure_included():
    """§4: 短分片不是 N/A,金额必须并入全局敞口。"""
    long = _long(5, "L")
    short = [_row(0, amount=100.0, prefix="S")]
    r = campaign_audit([long, short], seed=7, k=3)
    assert r["exposure"] == math.fsum([1.0] * 5 + [100.0])


def test_empty_campaign_not_ok():
    """空联审不得报 ok=True(空集≠审过)。"""
    r = campaign_audit([[], []], seed=1, k=5)
    assert r["ok"] is False


def test_sample_len_equals_k():
    """§5 贯穿: 联审对并集抽一次,样本长度=k,不是 k×分片数。"""
    s0 = _long(8, "A")
    s1 = _long(8, "B")
    r = campaign_audit([s0, s1], seed=11, k=5)
    assert len(r["sample"]) == 5


# ─── 非 gating 口径(切分合并 fsum) ───
def test_split_merge_matches_whole_fsum():
    """§4: 切分后合并敞口 == 整单 math.fsum(与累加顺序无关)。"""
    a = _row(0, amount=1e16, prefix="X")
    b = _row(1, amount=1.0, prefix="X")
    c = _row(2, amount=-1e16, prefix="X")
    whole = math.fsum([a["amount"], b["amount"], c["amount"]])
    r = campaign_audit([[a, b], [c]], seed=3, k=1)
    assert r["exposure"] == whole


# ─── 功能正确性 ───
def test_two_full_shards_ok():
    """两份都够 k 条时联审成立。"""
    r = campaign_audit([_long(6, "P"), _long(6, "Q")], seed=2, k=3)
    assert r["ok"] is True


def test_sample_ids_subset_of_union():
    """样本 id 必须来自并集。"""
    s0 = _long(6, "M")
    s1 = _long(6, "N")
    union_ids = {x["id"] for x in s0 + s1}
    r = campaign_audit([s0, s1], seed=9, k=4)
    assert {x["id"] for x in r["sample"]} <= union_ids


def test_campaign_reproducible():
    """§1: 同参数重跑逐位一致。"""
    shards = [_long(6, "U"), _long(6, "V")]
    a = campaign_audit(shards, seed=42, k=3)
    b = campaign_audit(shards, seed=42, k=3)
    assert [x["id"] for x in a["sample"]] == [x["id"] for x in b["sample"]]
    assert a["exposure"] == b["exposure"]
    assert a["ok"] is b["ok"]


def test_detail_reports_ratio():
    """detail 含已执行/总分片比例,未验证可追溯。"""
    r = campaign_audit([_long(6, "D"), _long(6, "E")], seed=4, k=3)
    assert "/" in r["detail"]
    assert "2" in r["detail"]
