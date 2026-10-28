"""双门 true_wall 判定 TDD(6/17 晚·硬化本会话核心学到的方法论)。

🔴 本会话实证教训:只用门 A(doubao pass@k==0)判 true_wall **不够**——会把
"容差墙/bucket-B 难倒题"(强模型也解不出·没正确 trace 可蒸)误判成蒸馏燃料。
p14 实证:doubao 0/7 + deepseek-v4-pro/qwen3.7-max 也全卡同一 max_diff 0.018。

双门(写进代码·防回退):
  门 A(S-诊断)= 良好 elicitation 下 doubao pass@k==0 且无洗门(= 现有 classify_task 的 true_wall)
  门 B(S-分拣)= ≥1 个强模型在同 harness 解出
  → distillation_fuel(蒸馏燃料)= 门 A ∧ 门 B
  → buyer_stump(bucket-B·买方难倒题·非燃料)= 门 A ∧ ¬门 B
"""
import pytest
from services.fde_triage import classify_distillation_fuel


def _d(uid, n, passed, gated=0):
    return {"task_uid": uid, "n_samples": n, "n_passed": passed, "n_correct_but_gated": gated}


def test_true_wall_plus_strong_solves_is_distillation_fuel():
    # 门A过(doubao 0/50)+ 门B过(强模型解出)→ 真蒸馏燃料
    r = classify_distillation_fuel(_d("t", 50, 0), strong_model_passed=True)
    assert r["bucket"] == "distillation_fuel"
    assert r["distill_candidate"] is True


def test_true_wall_but_strong_also_fails_is_buyer_stump_not_fuel():
    # p14 情形:门A过(doubao 0/7)但门B不过(强模型也解不出)→ bucket-B 买方难倒题·非燃料
    r = classify_distillation_fuel(_d("p14", 7, 0), strong_model_passed=False)
    assert r["bucket"] == "buyer_stump"
    assert r["distill_candidate"] is False


def test_doubao_solves_never_reaches_strong_gate():
    # 门A不过(doubao 能解·pseudo)→ 与门B无关·不是燃料(p13 情形)
    r = classify_distillation_fuel(_d("p13", 2, 1), strong_model_passed=True)
    assert r["bucket"] == "pseudo_wall"
    assert r["distill_candidate"] is False


def test_too_easy_short_circuits():
    r = classify_distillation_fuel(_d("e", 10, 9), strong_model_passed=False)
    assert r["bucket"] == "too_easy"
    assert r["distill_candidate"] is False


def test_gate_artifact_not_fuel_regardless_of_strong():
    # 洗门(0 真通过但正确被门拒)→ 永不燃料·不进门B
    r = classify_distillation_fuel(_d("g", 50, 0, gated=50), strong_model_passed=True)
    assert r["bucket"] == "gate_artifact"
    assert r["distill_candidate"] is False


def test_strong_unknown_keeps_candidate_pending():
    # 门B 未测(None)→ 不能宣称燃料·标 pending(诚实·不臆造)
    r = classify_distillation_fuel(_d("t", 50, 0), strong_model_passed=None)
    assert r["bucket"] == "true_wall_pending_strong_gate"
    assert r["distill_candidate"] is False
