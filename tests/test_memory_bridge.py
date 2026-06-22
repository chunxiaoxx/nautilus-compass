"""TDD for memory_bridge.py · 齿轮⑤ split-brain 桥(飞轮 sqlite learning → 文件语义库胶囊)。

纯逻辑 + 注入 fake ingest_fn·无需 live。live(读 sqlite obs + POST /v1/v14/ingest_obs)部署后接。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import memory_bridge as mb  # noqa: E402


# ---- 晋升门 should_bridge ----
def test_high_reward_bridges():
    assert mb.should_bridge({"reward": 1.0, "learning": "x"}) is True


def test_low_reward_blocked():
    assert mb.should_bridge({"reward": 0.5, "learning": "x"}) is False


def test_revoked_blocked():
    assert mb.should_bridge({"reward": 1.0, "revoked": True, "learning": "x"}) is False


def test_missing_reward_is_compat_pass():
    # 旧写法无 reward 字段 = 视作已验证(与 W2 compass_recall_pits 一致)
    assert mb.should_bridge({"learning": "x"}) is True


def test_garbage_reward_blocked():
    assert mb.should_bridge({"reward": "oops", "learning": "x"}) is False


# ---- obs_to_ingest_body ----
def test_body_has_content_and_tags():
    obs = {"family": "ale_ahc_ahc001", "learning": "use simulated annealing", "reward": 1.0, "source": "nautilus-prime-001"}
    b = mb.obs_to_ingest_body(obs)
    assert b["content"] == "use simulated annealing"
    assert b["project"] == mb.CAPSULE_PROJECT
    assert "family:ale_ahc_ahc001" in b["tags"]
    assert "reward:1" in b["tags"]
    assert "source:nautilus-prime-001" in b["tags"]
    assert "fleet-capsule" in b["tags"]
    assert b["drift"] == "green"


def test_body_includes_verdict_tag_when_present():
    b = mb.obs_to_ingest_body({"family": "f", "learning": "y", "reward": 1.0, "verdict": "solver_correctness"})
    assert any(t.startswith("verdict:solver_correctness") for t in b["tags"])


def test_body_name_and_desc_bounded():
    b = mb.obs_to_ingest_body({"family": "f", "learning": "z" * 999, "reward": 1.0})
    assert len(b["name"]) <= 80
    assert len(b["description"]) <= 200


def test_body_reads_reason_or_content_fallback():
    assert mb.obs_to_ingest_body({"reason": "r", "reward": 1.0})["content"] == "r"
    assert mb.obs_to_ingest_body({"content": "c", "reward": 1.0})["content"] == "c"


# ---- capsule_key (dedup) ----
def test_key_prefers_obs_id():
    assert mb.capsule_key({"obs_id": "ob_fw_1", "learning": "x"}) == "ob_fw_1"


def test_key_falls_back_to_family_text():
    k = mb.capsule_key({"family": "f", "learning": "abc"})
    assert k == "f::abc"


# ---- consolidate ----
def test_consolidate_filters_and_writes():
    written = []
    obs = [
        {"obs_id": "a", "reward": 1.0, "family": "f", "learning": "good1"},
        {"obs_id": "b", "reward": 0.3, "family": "f", "learning": "bad"},      # gate
        {"obs_id": "c", "reward": 1.0, "revoked": True, "learning": "rev"},    # gate
        {"obs_id": "d", "reward": 1.0, "family": "f", "learning": "good2"},
    ]
    stats = mb.consolidate(obs, lambda body: written.append(body))
    assert stats["written"] == 2
    assert stats["skipped_gate"] == 2
    assert stats["skipped_dup"] == 0
    assert [w["content"] for w in written] == ["good1", "good2"]


def test_consolidate_idempotent_via_seen():
    written = []
    seen = set()
    obs = [{"obs_id": "a", "reward": 1.0, "learning": "x"}]
    mb.consolidate(obs, lambda b: written.append(b), seen=seen)
    mb.consolidate(obs, lambda b: written.append(b), seen=seen)  # 第二轮同 obs
    assert len(written) == 1  # 只写一次
    assert "a" in seen


def test_consolidate_empty():
    stats = mb.consolidate([], lambda b: None)
    assert stats == {"written": 0, "skipped_gate": 0, "skipped_dup": 0, "keys": []}
