"""P0 记忆胶囊防退化(compass client 层)· 2026-06-22 · compass turf

design doc §6 接线点(`docs/plans/2026-06-21-memory-capsule-evolution-design.md`):
- W1 write_learning:附 verdict 元数据(reward/bucket/score/source)+ 晋升门(reward<阈拒写)
- W2 compass_recall_pits:质量过滤(丢 revoked / 低 reward)+ 质量优先排序
- 单条 revoke:revoke_learning 写 tombstone(复用 /v1/observations·无需 serving 改)· recall 自动屏蔽

keystone:错经验不再被 W2 跨 agent 复利成毒 + 可撤销。
纯逻辑层 TDD(monkeypatch _http/_token/_user_id·不打网络)。
"""
import importlib
import pytest

cfm = importlib.import_module("compass_fleet_memory")


@pytest.fixture
def stub_io(monkeypatch):
    """挡掉网络/凭据·捕获所有 POST body·GET 返回可注入 hits。"""
    posts = []
    state = {"hits": [], "post_status": 201}

    def fake_http(method, url, body=None, token=None, timeout=30):
        if method == "POST":
            posts.append(body)
            return state["post_status"], {"obs_id": body.get("obs_id")}
        return 200, {"hits": state["hits"]}

    monkeypatch.setattr(cfm, "_http", fake_http)
    monkeypatch.setattr(cfm, "_token", lambda: "tok")
    monkeypatch.setattr(cfm, "_user_id", lambda: "u1")
    return posts, state


def _hit(learning, reward=None, revoked=None, revokes=None, agent_id="agA", obs_id=None):
    content = {"learning": learning, "family": "requests"}
    if reward is not None:
        content["reward"] = reward
    if revoked is not None:
        content["revoked"] = revoked
    if revokes is not None:
        content["revokes"] = revokes
    h = {"agent_id": agent_id, "content_or_encrypted": content}
    if obs_id is not None:
        h["obs_id"] = obs_id
    return h


# ── W1:晋升门 + verdict 元数据 ──

def test_write_gate_blocks_low_reward(stub_io):
    posts, _ = stub_io
    out = cfm.write_learning("agA", "requests", "坏经验", reward=0.2)
    assert out is None              # 拒写
    assert posts == []              # 没有发出 POST(错经验不入库)


def test_write_stores_verdict_metadata(stub_io):
    posts, _ = stub_io
    out = cfm.write_learning("agA", "requests", "好经验",
                             reward=1.0, bucket="grounded", score=0.95, source="rsi_two_arm")
    assert out is not None
    c = posts[0]["content"]
    assert c["reward"] == 1.0 and c["bucket"] == "grounded"
    assert c["score"] == 0.95 and c["source"] == "rsi_two_arm"
    assert c["revoked"] is False


def test_write_backward_compat_default_reward(stub_io):
    posts, _ = stub_io
    out = cfm.write_learning("agA", "requests", "默认就是已验证正确")
    assert out is not None
    assert posts[0]["content"]["reward"] == 1.0   # 默认 1.0 → 过门(旧调用不传 reward)


# ── W2:质量过滤 + 排序 ──

def test_recall_quality_sort_high_reward_first(stub_io):
    _, state = stub_io
    state["hits"] = [
        _hit("低质教训", reward=0.7, agent_id="agLow"),
        _hit("高质教训", reward=1.0, agent_id="agHigh"),
    ]
    pits = cfm.compass_recall_pits("requests")
    assert [p["reason"] for p in pits] == ["高质教训", "低质教训"]


def test_recall_drops_below_min_reward(stub_io):
    _, state = stub_io
    state["hits"] = [_hit("及格", reward=1.0), _hit("不及格", reward=0.3)]
    pits = cfm.compass_recall_pits("requests", min_reward=0.5)
    assert [p["reason"] for p in pits] == ["及格"]


def test_recall_backward_compat_missing_reward_kept(stub_io):
    _, state = stub_io
    state["hits"] = [_hit("旧 obs 无 reward 字段")]   # 兼容旧写法(默认视作已验证)
    pits = cfm.compass_recall_pits("requests")
    assert len(pits) == 1 and pits[0]["reason"] == "旧 obs 无 reward 字段"


def test_recall_contract_only_item_id_and_reason(stub_io):
    _, state = stub_io
    state["hits"] = [_hit("教训", reward=1.0, agent_id="agA")]
    pits = cfm.compass_recall_pits("requests")
    # build_grounding_block 契约:每 pit 恰好 {item_id, reason}
    assert set(pits[0].keys()) == {"item_id", "reason"}
    assert pits[0]["item_id"] == "agA"


# ── 单条 revoke(tombstone)──

def test_revoke_writes_tombstone(stub_io):
    posts, _ = stub_io
    oid = cfm.revoke_learning("agA", "requests", "坏经验文本")
    assert oid is not None
    c = posts[0]["content"]
    assert c["revoked"] is True and c["revokes"] == "坏经验文本"


def test_recall_suppresses_revoked_by_substring(stub_io):
    _, state = stub_io
    state["hits"] = [
        _hit("requests 连接池泄漏要 close session", reward=1.0, agent_id="agBad"),
        _hit("好教训保留", reward=1.0, agent_id="agOk"),
        _hit("", reward=1.0, revoked=True, revokes="连接池泄漏", agent_id="agTomb"),
    ]
    pits = cfm.compass_recall_pits("requests")
    reasons = [p["reason"] for p in pits]
    assert "好教训保留" in reasons
    assert not any("连接池泄漏" in r for r in reasons)   # 被 tombstone 屏蔽
    assert "" not in reasons                              # tombstone 本身不当 pit


def test_recall_suppresses_revoked_by_obs_id(stub_io):
    _, state = stub_io
    state["hits"] = [
        _hit("按 obs_id 撤销", reward=1.0, obs_id="ob_fw_requests_111", agent_id="agBad"),
        _hit("", reward=1.0, revoked=True, revokes="ob_fw_requests_111", agent_id="agTomb"),
    ]
    pits = cfm.compass_recall_pits("requests")
    assert pits == []   # 唯一真 pit 被按 obs_id 撤销


# ── fail-soft 保持(记忆服务抖动不停摆飞轮)──

def test_recall_http_500_returns_empty(stub_io, monkeypatch):
    monkeypatch.setattr(cfm, "_http", lambda *a, **k: (500, {}))
    assert cfm.compass_recall_pits("requests") == []
