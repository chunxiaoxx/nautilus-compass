"""QC judge JSON 健壮解析单测(2026-06-22)· 修 c4 "judge error: Unterminated string" bug。

根因(实测 6/22 dogfood c4):judge_fn 抽 raw[s:e+1] 后 json.loads·LLM reason 含裸换行/
截断 → JSONDecodeError "Unterminated string" → 整项判 fail(误伤合法提交)。
修:parse_judge_json 健壮兜底(去控制字符 + regex fallback pass)·真不可解析才 None。
"""
from __future__ import annotations

from services.fde_scorer_runner import parse_judge_json


def test_clean_json():
    out = parse_judge_json('{"pass": true, "reason": "ok"}')
    assert out == {"pass": True, "reason": "ok"}


def test_pass_false():
    out = parse_judge_json('Here: {"pass": false, "reason": "missing source"} done')
    assert out["pass"] is False


def test_raw_newline_in_reason_unterminated_recovered():
    # 裸换行(就是 c4 的 Unterminated string 根因)→ 去控制字符后可解析
    raw = '{"pass": false, "reason": "line1\nline2 多行原因"}'
    out = parse_judge_json(raw)
    assert out is not None and out["pass"] is False


def test_truncated_json_regex_fallback():
    # 截断(reason 没收尾)→ regex 兜底抓 pass
    raw = '{"pass": true, "reason": "this got cut off mid str'
    out = parse_judge_json(raw)
    assert out is not None and out["pass"] is True


def test_reasoning_prefix_with_pass_phrase():
    # 无合法 JSON 但文本含 pass:true → regex 兜底
    raw = "Let me think... the answer satisfies the rule. pass: true"
    out = parse_judge_json(raw)
    assert out is not None and out["pass"] is True


def test_truly_unparseable_returns_none():
    assert parse_judge_json("完全没有判定信息的一段话") is None
    assert parse_judge_json("") is None
