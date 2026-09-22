# -*- coding: utf-8 -*-
"""BC1 判分器 — 考生 answers.json → 三态成绩单(PROTOCOL 判据 2/5)。

用法:python verify_bc1.py answers.json [--split public|all]
answers 格式:{"T11-0": {"answer_json": {...}} 或 {"answer": "..."}, ...}
三态:PASS(与 expected 深等,数值容差 1e-9)/FAIL(不等)/
     U(缺题/JSON 解析失败——不可算不充正分)。
U 规则:考生未交该题、或交的 JSON 无法解析 = U。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
TOL = 1e-9


def canon(v):
    """排序无关规范化:list 排序、dict 键排序、float round(6)。"""
    if isinstance(v, dict):
        return {k: canon(x) for k, x in sorted(v.items())}
    if isinstance(v, list):
        return sorted((canon(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True))
    if isinstance(v, float):
        return round(v, 6)
    return v


def deep_eq(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) \
            and not isinstance(a, bool) and not isinstance(b, bool):
        return abs(a - b) <= TOL
    if type(a) != type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(deep_eq(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_eq(x, y) for x, y in zip(
            sorted(a, key=lambda t: json.dumps(t, sort_keys=True)),
            sorted(b, key=lambda t: json.dumps(t, sort_keys=True))))
    return a == b


def load_answers(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for qid, payload in raw.items():
        if isinstance(payload, dict) and "answer_json" in payload:
            out[qid] = {"target": "answer_json", "raw": payload["answer_json"]}
        elif isinstance(payload, dict) and "answer" in payload:
            out[qid] = {"target": "answer", "raw": payload["answer"]}
        else:
            out[qid] = {"target": "?", "raw": payload}
    return out


def main():
    answers_path = sys.argv[1]
    split = "public"
    if "--split" in sys.argv:
        split = sys.argv[sys.argv.index("--split") + 1]
    ds = json.loads((HERE / "decision_set.json").read_text(encoding="utf-8"))
    items = [it for it in ds["items"]
             if split == "all" or it.get("public")]
    answers = load_answers(answers_path)

    results, counts = {}, {"PASS": 0, "FAIL": 0, "U": 0}
    for it in items:
        qid = it["qid"]
        target = it["check"]["spec"]["target"]
        ans = answers.get(qid)
        if ans is None or ans["target"] != target:
            results[qid] = "U"
        else:
            raw = ans["raw"]
            # only answer_json targets may arrive as a JSON string to re-parse;
            # a plain string answer IS the answer
            if target == "answer_json" and isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except (ValueError, TypeError):
                    results[qid] = "U"
                    counts["U"] += 1
                    continue
            results[qid] = "PASS" if deep_eq(canon(raw), canon(it["expected"])) else "FAIL"
        counts[results[qid]] += 1

    by_dim = {}
    for it in items:
        d = by_dim.setdefault(it["dim"], {"PASS": 0, "FAIL": 0, "U": 0, "n": 0})
        d[results[it["qid"]]] += 1
        d["n"] += 1

    scorecard = {"split": split, "n": len(items), "counts": counts,
                 "by_dim": by_dim, "results": results,
                 "score": counts["PASS"], "max": len(items)}
    out = HERE / f"scorecard_{split}.json"
    out.write_text(json.dumps(scorecard, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="\n")
    print(f"BC1 scorecard [{split}]: PASS={counts['PASS']} FAIL={counts['FAIL']} "
          f"U={counts['U']} / {len(items)}")
    for d, v in sorted(by_dim.items()):
        print(f"  {d}: {v['PASS']}/{v['n']} (U={v['U']})")


if __name__ == "__main__":
    main()
