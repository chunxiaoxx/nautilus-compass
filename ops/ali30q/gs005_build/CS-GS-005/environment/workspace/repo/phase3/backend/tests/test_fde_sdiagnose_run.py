"""S-诊断 runner 纯逻辑 TDD(6/18·p13 pass@k true_wall sprint)。

runner = net-new orchestration:doubao 采样 → 每候选 GPU kb_eval → 聚合 → fde_triage 定桶。
本测试只覆盖**纯逻辑**(代码抽取 + kb_eval 结果→triage 契约聚合);
网络/ssh 编排走 CLI integration(真跑·非单元)。

聚合死口径(对齐 GPU box triage_aggregate.classify_candidate):
  pass_final == True                       → passed            (correctness + strict-1e-3 + 非 suspect 全过)
  pass_final == False and pass_correct_raw → correct_but_gated (correctness 过·G2 >2× 门拒=洗门)
  否则                                     → correctness_fail  (true_wall 分子)
"""
import pytest

from services.fde_sdiagnose_run import (extract_code, get_completer,
                                         summarize_candidate_results)


def test_get_completer_dispatch():
    fn, model = get_completer("bailian", "deepseek-v4-pro")
    assert callable(fn) and model == "deepseek-v4-pro"
    fn, model = get_completer("ark", "doubao-seed-2.0-pro")
    assert callable(fn) and model == "doubao-seed-2.0-pro"


def test_get_completer_unknown_provider():
    with pytest.raises(ValueError):
        get_completer("openai", "gpt-x")


def test_extract_code_python_block():
    text = "解释...\n```python\nclass ModelNew:\n    pass\n```\n收尾"
    assert extract_code(text).strip() == "class ModelNew:\n    pass"


def test_extract_code_bare_block_no_lang():
    text = "```\nx = 1\n```"
    assert extract_code(text).strip() == "x = 1"


def test_extract_code_no_block_returns_raw():
    assert extract_code("没有代码块").strip() == "没有代码块"


def test_extract_code_picks_block_with_modelnew():
    # 多个块时优先含 ModelNew 的(doubao 常先给示例块再给答案)
    text = "```python\nprint('demo')\n```\n然后\n```python\nclass ModelNew: pass\n```"
    assert "ModelNew" in extract_code(text)


def test_summarize_all_correctness_fail_is_true_wall_numerator():
    results = [{"pass_final": False, "reason": "official_eval_fail"} for _ in range(10)]
    s = summarize_candidate_results(results)
    assert s["n_samples"] == 10
    assert s["n_passed"] == 0
    assert s["n_correct_but_gated"] == 0
    assert s["n_correctness_fail"] == 10


def test_summarize_passed_counts():
    results = [
        {"pass_final": True, "reason": "pass"},
        {"pass_final": True, "reason": "pass"},
        {"pass_final": False, "reason": "official_eval_fail"},
    ]
    s = summarize_candidate_results(results)
    assert s["n_passed"] == 2
    assert s["n_correctness_fail"] == 1
    assert s["n_correct_but_gated"] == 0


def test_summarize_correct_but_gated_is_washout_not_truewall():
    # G2 suspect cap:correctness 过但被 >2× 门拒 → 洗门信号
    results = [
        {"pass_final": False, "pass_correct_raw": True,
         "reason": "suspect_excessive_speedup: 5.0x > 2.0x cap"},
        {"pass_final": False, "reason": "precision_degraded"},
    ]
    s = summarize_candidate_results(results)
    assert s["n_correct_but_gated"] == 1
    assert s["n_correctness_fail"] == 1
    assert s["n_passed"] == 0


def test_summarize_skips_errored_results():
    # ark_error / eval 崩溃的样本不计入分母(诚实:只统计真正跑出验证结果的)
    results = [
        {"pass_final": False, "reason": "official_eval_fail"},
        {"error": "ark_error: timeout"},
    ]
    s = summarize_candidate_results(results)
    assert s["n_samples"] == 1
    assert s["n_errored"] == 1
