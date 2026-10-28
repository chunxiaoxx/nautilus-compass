"""S-诊断 三桶分类器 TDD(6/17·RSI 蒸馏飞轮 gate)。

输入契约(platform-soul 提出·compass benchmark_verifier 对齐):
  每题 pass@大k 聚合 = {
    "task_uid": str,
    "n_samples": int,            # doubao 高温采样数(50~250)
    "n_passed": int,             # 完整通过验证器(correctness + 所有门)的样本数
    "n_correct_but_gated": int,  # 答案正确但被"非正确性门"(perf >2×/format)拒的样本数 = 洗门信号
    "pass_at_1": float | None,   # 可选·缺省用 n_passed/n_samples 估
  }
分四桶(设计 2026-06-14 §1+§4):
  真能力墙 true_wall      pass@大k=0 且无洗门 → 蒸馏候选(唯一破墙=蒸馏)
  伪能力墙 pseudo_wall    pass@大k>0 但 pass@1 低 → best-of-N/verifier/RFT 有效
  洗门     gate_artifact  正确却被门拒(doubao 其实会)→ 实质 C·绝不喂蒸馏·挑出净增交付
  太易     too_easy       pass 率高(>买方难倒线 0.6)→ 丢
"""
import pytest
from services.fde_triage import classify_task, triage_batch, TOO_EASY_PASS_RATE


def _d(uid, n, passed, gated=0, p1=None):
    return {"task_uid": uid, "n_samples": n, "n_passed": passed,
            "n_correct_but_gated": gated, "pass_at_1": p1}


def test_true_wall_zero_pass_no_gate():
    r = classify_task(_d("t1", 200, 0, gated=0))
    assert r["bucket"] == "true_wall"
    assert r["distill_candidate"] is True


def test_gate_artifact_correct_but_gated_dominates():
    # doubao 5/5 正确却撞 >2× 门 → 洗门·非真墙·不喂蒸馏
    r = classify_task(_d("t2", 200, 0, gated=200))
    assert r["bucket"] == "gate_artifact"
    assert r["distill_candidate"] is False


def test_gate_artifact_priority_over_true_wall_when_zero_passed():
    # 0 真通过但有正确被门拒 → 表面"真墙"实为洗门·必须洗门优先
    r = classify_task(_d("t3", 100, 0, gated=3))
    assert r["bucket"] == "gate_artifact"


def test_pseudo_wall_some_pass_low_rate():
    # 偶尔通过(会但不稳)→ 伪墙
    r = classify_task(_d("t4", 200, 10, gated=0))  # 5% pass
    assert r["bucket"] == "pseudo_wall"
    assert r["distill_candidate"] is False


def test_too_easy_high_pass_rate():
    r = classify_task(_d("t5", 200, 160, gated=0))  # 80% > 0.6
    assert r["bucket"] == "too_easy"


def test_too_easy_boundary_at_threshold():
    # 恰好等于阈值不算太易(买方:pass@5 ≤ 0.6 才算难倒)
    r = classify_task(_d("t6", 100, int(TOO_EASY_PASS_RATE * 100), gated=0))
    assert r["bucket"] == "pseudo_wall"


def test_pass_at_1_explicit_overrides_estimate():
    # 显式 pass_at_1 高 → 太易(即便 n_passed/n_samples 低)
    r = classify_task(_d("t7", 200, 5, gated=0, p1=0.9))
    assert r["bucket"] == "too_easy"


def test_some_pass_with_gated_still_pseudo_not_artifact():
    # 既有真通过又有被门拒 → 它能通过·伪墙(洗门只在 0 真通过时夺权)
    r = classify_task(_d("t8", 200, 8, gated=5))
    assert r["bucket"] == "pseudo_wall"


def test_zero_samples_guarded():
    with pytest.raises(ValueError):
        classify_task(_d("t9", 0, 0))


def test_n_passed_gt_samples_guarded():
    with pytest.raises(ValueError):
        classify_task(_d("t10", 5, 9))


def test_triage_batch_groups_and_summarizes():
    tasks = [
        _d("a", 200, 0, gated=0),     # true_wall
        _d("b", 200, 0, gated=200),   # gate_artifact
        _d("c", 200, 10, gated=0),    # pseudo_wall
        _d("d", 200, 180, gated=0),   # too_easy
        _d("e", 200, 0, gated=0),     # true_wall
    ]
    out = triage_batch(tasks)
    assert set(out["buckets"].keys()) == {"true_wall", "pseudo_wall", "gate_artifact", "too_easy"}
    assert sorted(out["buckets"]["true_wall"]) == ["a", "e"]
    assert out["buckets"]["gate_artifact"] == ["b"]
    assert out["summary"]["true_wall"] == 2
    assert out["summary"]["distill_candidates"] == 2  # 只有 true_wall 是蒸馏候选
    assert out["summary"]["total"] == 5
