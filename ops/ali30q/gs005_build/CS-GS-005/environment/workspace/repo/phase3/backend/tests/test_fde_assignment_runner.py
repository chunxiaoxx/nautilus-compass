"""S1 effect runner · 纯解析部分单测(_plain + 派活行过滤/字段映射).

HTTP/飞书 effect 不测(mock urlopen 覆盖 read 解析逻辑即可)。
"""
import services.fde_assignment_runner as r


def test_plain_handles_richtext_list_and_scalar():
    assert r._plain([{"text": "跨端"}, {"text": "一致性"}]) == "跨端一致性"
    assert r._plain("L2") == "L2"
    assert r._plain(None) == ""


def test_source_reads_only_pending_rows_and_maps_fields(monkeypatch):
    fake_items = {
        "data": {"items": [
            {"record_id": "rec1", "fields": {
                "task_uid": "expert_t1_x", "标题": [{"text": "题X"}],
                "业务线": "1", "一级类目": "互联网与平台业务", "三级领域": "跨端",
                "L级": "L2", "指派专家": "chunxiao",
                "验收标准": [{"text": "c1 否决"}], "状态": "待派单"}},
            {"record_id": "rec2", "fields": {
                "task_uid": "expert_t1_done", "状态": "已派单"}},  # 非待派单→跳
        ]}
    }
    monkeypatch.setattr(r, "_http", lambda *a, **k: fake_items)
    src = r.FeishuAssignmentSource("tok", "appX", "tblX")
    rows = src.read_assignment_rows()
    assert len(rows) == 1
    row = rows[0]
    assert row["task_uid"] == "expert_t1_x"
    assert row["title"] == "题X"
    assert row["acceptance"] == "c1 否决"
    assert row["level"] == "L2"
    assert src.record_ids["expert_t1_x"] == "rec1"  # 写回用


def test_source_rows_feed_build_dispatch_end_to_end(monkeypatch):
    """读出来的行能直接喂 build_assignment_dispatch(契约对齐 sync_assignments)。"""
    from services.fde_assignment import build_assignment_dispatch
    fake = {"data": {"items": [{"record_id": "r", "fields": {
        "task_uid": "expert_t2_k", "标题": "教案K", "业务线": "2",
        "一级类目": "金融", "三级领域": "风控", "L级": "L2",
        "指派专家": "chunxiao", "验收标准": "5部分齐", "状态": "待派单"}}]}}
    monkeypatch.setattr(r, "_http", lambda *a, **k: fake)
    rows = r.FeishuAssignmentSource("t", "a", "b").read_assignment_rows()
    body = build_assignment_dispatch(rows[0])
    assert body is not None and body["task_uid"] == "expert_t2_k"


def test_claim_fn_idempotent_when_already_claimed_by_same_expert(monkeypatch):
    """C1/I2:任务已被同一专家占座(409 错误含 expert:X)→ 幂等成立·不报 lost。"""
    monkeypatch.setattr(r, "_http", lambda *a, **k: {
        "success": False,
        "error": "task already claimed (claimed_by=expert:chunxiao)"})
    claim = r.make_claim_fn("http://x")
    claim("expert_t2_k", "expert:chunxiao")  # 不抛 = ok


def test_claim_fn_raises_when_claimed_by_agent(monkeypatch):
    """C1:被 agent(kairos)抢 → 抛 → sync_assignments 归 lost_to_agent。"""
    import pytest
    monkeypatch.setattr(r, "_http", lambda *a, **k: {
        "success": False, "error": "task already claimed (claimed_by=kairos)"})
    claim = r.make_claim_fn("http://x")
    with pytest.raises(RuntimeError):
        claim("expert_t2_k", "expert:chunxiao")


def test_http_returns_json_envelope_on_httperror(monkeypatch):
    """C1:urlopen 对 409 抛 HTTPError·_http 捕获并返 body envelope(让 success 检查活)。"""
    import io
    import urllib.error

    def fake_urlopen(req, timeout=30):
        raise urllib.error.HTTPError(
            req.full_url, 409, "Conflict", {},
            io.BytesIO(b'{"success": false, "error": "already claimed"}'))
    monkeypatch.setattr(r.urllib.request, "urlopen", fake_urlopen)
    res = r._http("POST", "http://x/claim", body={"task_uid": "t"})
    assert res["success"] is False and "already claimed" in res["error"]
