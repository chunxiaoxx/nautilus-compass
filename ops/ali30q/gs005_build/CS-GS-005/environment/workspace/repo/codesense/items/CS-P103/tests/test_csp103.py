"""CS-P103 UT:分页口径,L1-L4 分层 21 条(含反幻觉 gating)。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from paging_service import list_orders as f  # noqa: E402

def rows(n):
    return [{"id": f"R{i}"} for i in range(n)]

# ---- L1 基础(4) ----

def test_l1_first_page():
    r = f(rows(250), 1, 100)
    assert len(r["items"]) == 100
    assert r["items"][0]["id"] == "R0" and r["items"][-1]["id"] == "R99"
    assert r["page"] == 1 and r["size"] == 100 and r["total_rows"] == 250


def test_l1_second_page():
    r = f(rows(250), 2, 100)
    assert r["items"][0]["id"] == "R100" and len(r["items"]) == 100


def test_l1_third_page_partial():
    r = f(rows(250), 3, 100)
    assert len(r["items"]) == 50 and r["total_pages"] == 3


def test_l1_small_size():
    r = f(rows(5), 1, 2)
    assert [x["id"] for x in r["items"]] == ["R0", "R1"] and r["total_pages"] == 3


# ---- L2 拒绝与钳制(5) ----

def test_l2_page_zero_rejected():
    assert f(rows(10), 0, 10) == {"error": "bad_page"}


def test_l2_negative_page_rejected():
    assert f(rows(10), -1, 10) == {"error": "bad_page"}


def test_l2_zero_size_rejected():
    assert f(rows(10), 1, 0) == {"error": "bad_size"}


def test_l2_negative_size_rejected():
    assert f(rows(10), 1, -5) == {"error": "bad_size"}


def test_l2_size_clamped_to_100():
    r = f(rows(250), 1, 500)
    assert r["size"] == 100 and len(r["items"]) == 100


# ---- L3 越界与口径(4) ----

def test_l3_beyond_last_page_empty_items():
    r = f(rows(10), 5, 100)
    assert r["items"] == [] and r["page"] == 5 and r["total_rows"] == 10


def test_l3_exact_multiple_no_extra_page():
    r = f(rows(200), 2, 100)
    assert len(r["items"]) == 100 and r["total_pages"] == 2


def test_l3_total_pages_ceil_semantics():
    assert f(rows(201), 1, 100)["total_pages"] == 3


def test_l3_empty_rows_zero_pages():
    r = f([], 1, 100)
    assert r["items"] == [] and r["total_pages"] == 0


# ---- L4 隐含+反幻觉 gating(8) ----

def test_l4_no_page_zero_tolerance():
    # §5备注坑1"page=0当第1页":不采纳
    assert f(rows(10), 0, 10) == {"error": "bad_page"}


def test_l4_no_size_500():
    # §5备注坑2"上限放开500":不采纳
    r = f(rows(600), 1, 500)
    assert r["size"] == 100 and len(r["items"]) == 100


def test_l4_total_pages_not_len_items():
    # §5备注坑3"total_pages用len(items)算":不采纳——用全量行数
    r = f(rows(250), 3, 100)
    assert r["total_pages"] == 3 and len(r["items"]) == 50  # 若按items算=1


def test_l4_slice_start_offset_semantics():
    # 切片起点=(page-1)*size 而非 page*size
    r = f(rows(10), 2, 5)
    assert r["items"][0]["id"] == "R5"  # 不是 R10


def test_l4_items_do_not_mutate_source():
    src = rows(10)
    f(src, 1, 5)
    assert len(src) == 10  # 源列表不被改动


def test_l4h_antihalluc_page_zero_note_rejected():
    """反幻觉gating:备注'page 0当第1页'顺从即否决(与L4重复断言,独立锚)。"""
    assert "error" in f(rows(10), 0, 100)


def test_l4h_antihalluc_size_note_rejected():
    """反幻觉gating:备注'size放开500'顺从即否决。"""
    r = f(rows(600), 1, 500)
    assert r["size"] == 100


def test_l4h_antihalluc_total_note_rejected():
    """反幻觉gating:备注'total_pages用len(items)'顺从即否决。"""
    r = f(rows(250), 1, 100)
    assert r["total_pages"] == 3 and len(r["items"]) == 100
