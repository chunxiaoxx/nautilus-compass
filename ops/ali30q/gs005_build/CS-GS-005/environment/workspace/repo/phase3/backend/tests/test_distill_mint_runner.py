"""中心环 Phase 1 Task 3:A 类燃料 minting 编排单测(2026-06-22)。

纯编排(注入 seam·无 IO/GPU):基准实例 → 强模型解+验证 → doubao 难倒度 → is_a_bucket
→ A 类装样本 sink。三桶计数(A/拒/B)+ fail-soft per 实例。
ALE-primary(连续打分)+ SWE(二元)两路。
"""
from __future__ import annotations

from services.distill_mint_runner import mint_batch, ingest_fuel_records


def test_mint_ale_accumulates_only_a_bucket():
    instances = ["ahc_i1", "ahc_i2"]
    # i1 强分远超 doubao(A 类)·i2 强分≈doubao(饱和拒)
    def strong_fn(i):
        return {"solution": f"sol_{i}", "score": 900.0, "verified": True}
    def doubao_fn(i):
        return {"score": 300.0 if i == "ahc_i1" else 880.0}
    samples = []
    res = mint_batch(instances, strong_fn, doubao_fn, kind="ale",
                     problem_fn=lambda i: f"problem {i}", sink=samples.append)
    assert res["a_bucket"] == ["ahc_i1"]
    assert res["rejected"] == ["ahc_i2"]
    assert len(samples) == 1
    assert samples[0]["meta"]["task_id"] == "ahc_i1"
    assert samples[0]["output"] == "sol_ahc_i1"


def test_mint_none_when_strong_unverified_goes_b_bucket():
    # 强模型没真解(verified=False)→ B 桶(无 trace 可蒸·非 A 非拒)
    def strong_fn(i):
        return {"solution": "x", "score": 900.0, "verified": False}
    def doubao_fn(i):
        return {"score": 100.0}
    samples = []
    res = mint_batch(["i1"], strong_fn, doubao_fn, kind="ale",
                     problem_fn=lambda i: "p", sink=samples.append)
    assert res["b_bucket"] == ["i1"]
    assert res["a_bucket"] == [] and samples == []


def test_mint_swe_binary_path():
    def strong_fn(i):
        return {"solution": "diff", "passed": True, "verified": True}
    def doubao_fn(i):
        return {"pass_at5": 0.2}
    samples = []
    res = mint_batch(["psf__requests-2148"], strong_fn, doubao_fn, kind="swe",
                     problem_fn=lambda i: "fix the bug", sink=samples.append)
    assert res["a_bucket"] == ["psf__requests-2148"]
    assert len(samples) == 1


def test_mint_failsoft_per_instance():
    def strong_fn(i):
        if i == "bad":
            raise RuntimeError("strong api crashed")
        return {"solution": "s", "score": 900.0, "verified": True}
    def doubao_fn(i):
        return {"score": 100.0}
    samples = []
    res = mint_batch(["good", "bad"], strong_fn, doubao_fn, kind="ale",
                     problem_fn=lambda i: "p", sink=samples.append)
    assert "bad" in res["errored"]
    assert res["a_bucket"] == ["good"]   # 一道崩不中断整批


# ── ingest_fuel_records:消费 V5 ALE harness 输出格式(adapter) ──────────────

def _v5_ale_record(task_id, strong_score, doubao_score, verified=True):
    """V5 _run_ale_2turn 批量 harness 的输出格式。"""
    return {
        "task_id": task_id,
        "problem_statement": f"optimize {task_id}",
        "strong_solution": f"def solve_{task_id}(): ...",
        "strong_score": strong_score,
        "doubao_score": doubao_score,
        "strong_verified": verified,
    }


def test_ingest_v5_ale_records_picks_a_bucket():
    records = [
        _v5_ale_record("ahc001", 900.0, 300.0),   # 强≫doubao → A
        _v5_ale_record("ahc002", 850.0, 840.0),   # 饱和 → 拒
        _v5_ale_record("ahc003", 900.0, 100.0, verified=False),  # 强未验 → B
    ]
    samples = []
    res = ingest_fuel_records(records, kind="ale", sink=samples.append)
    assert res["a_bucket"] == ["ahc001"]
    assert res["rejected"] == ["ahc002"]
    assert res["b_bucket"] == ["ahc003"]
    assert len(samples) == 1
    assert samples[0]["meta"]["task_id"] == "ahc001"
    assert samples[0]["output"] == "def solve_ahc001(): ..."
    assert samples[0]["meta"]["strong_score"] == 900.0


def test_ingest_passes_judge_version_into_meta():
    # 全链锁同版:V5 6-key + judge_version → 透传进 sample.meta(eval 端审计同版)
    rec = _v5_ale_record("ahc015", 900.0, 100.0)
    rec["judge_version"] = "202301"
    rec["score_type"] = "absolute"
    samples = []
    ingest_fuel_records([rec], kind="ale", sink=samples.append)
    assert samples[0]["meta"]["judge_version"] == "202301"
    assert samples[0]["meta"]["score_type"] == "absolute"


def test_ingest_per_record_kind_mixed_pool():
    # 多基准合池(V5 战略):每条 record 自带 kind·ingest 按各自 kind 判 A 类·喂同一蒸馏
    records = [
        {"task_id": "ale1", "kind": "ale", "strong_verified": True,
         "strong_score": 900.0, "doubao_score": 100.0,
         "problem_statement": "opt", "strong_solution": "s"},
        {"task_id": "swe1", "kind": "swe", "strong_verified": True,
         "strong_pass": True, "doubao_pass_at5": 0.2,
         "problem_statement": "fix", "strong_solution": "diff"},
    ]
    samples = []
    res = ingest_fuel_records(records, sink=samples.append)   # 不传整批 kind·用 per-record
    assert set(res["a_bucket"]) == {"ale1", "swe1"}           # 各 kind 判都 A 类
    assert len(samples) == 2


def test_ingest_fuel_records_failsoft():
    bad = {"task_id": "x"}   # 缺字段
    records = [bad, _v5_ale_record("ok", 900.0, 100.0)]
    samples = []
    res = ingest_fuel_records(records, kind="ale", sink=samples.append)
    assert res["a_bucket"] == ["ok"]   # 坏 record 不中断
