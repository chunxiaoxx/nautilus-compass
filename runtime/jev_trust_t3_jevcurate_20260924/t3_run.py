# -*- coding: utf-8 -*-
"""T3 mini 校准:jev-curate reasoning-math 5 行(协议见 PROTOCOL.md)。

主批 model=jev-1.13.0(生产同构);对照批 model=jev-latest(预注册可选项)。
"""
import json
import time
from pathlib import Path

from jev_trust import TrustedJev

OUT = Path(__file__).parent
KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"

ROWS = [
    {"rid": "R1", "text": "Let f(x) = x^2. By taking the derivative with respect to x, f'(x) = 2x.",
     "y_circ": 0, "d_depth": 4,
     "mock": {"noul": 0.05, "score": 4.8, "confidence": 0.95}},
    {"rid": "R2", "text": "P is true because P is valid, therefore P is established.",
     "y_circ": 1, "d_depth": 1,
     "mock": {"noul": 0.95, "score": 4.0, "confidence": 0.90}},
    {"rid": "R3", "text": "The answer is obviously 42, trust me on this.",
     "y_circ": 0, "d_depth": 1,
     "mock": {"noul": 0.10, "score": 2.0, "confidence": 0.90}},
    {"rid": "R4", "text": "Step 1: Compute matrix determinant. Step 2: Invert matrix.",
     "y_circ": 0, "d_depth": 2,
     "mock": {"noul": 0.10, "score": 4.5, "confidence": 0.30}},
    {"rid": "R5", "text": "Let a = 1 and b = 2. Then a + b = 3.",
     "y_circ": 0, "d_depth": 2,
     "mock": None},  # mock response 缺 reasoning_depth(fail-closed 测试)
]

QUESTIONS = {
    "has_circular_reasoning": {
        "type": "noul",
        "instructions": ("Does this solution or reasoning trace contain circular "
                         "reasoning, tautological leaps, or assume the conclusion "
                         "in the premise?"),
        "criteria": {"true": "Contains circular derivations or assumes the conclusion to prove itself",
                     "false": "Rigorous step-by-step reasoning from premises to conclusion"},
    },
    "reasoning_depth": {
        "type": "score",
        "instructions": "Rate the mathematical and logical rigor of this explanation.",
        # 探针实测:criteria 必须为字符串数组,服务端按 0-4 标尺回 legend
        "criteria": ["Superficial, hand-wavy, or incorrect calculations",
                     "Basic answer with missing intermediate steps",
                     "Sound derivation with standard detail",
                     "Clear, comprehensive step-by-step logic",
                     "Flawless, formal, and pedagogical mathematical rigor"],
    },
}


def run_batch(model, log_name):
    api_key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]
    jev = TrustedJev(api_key=api_key, domain="jev-curate-reasoning-math-t3",
                     log_path=str(OUT / log_name), model=model)
    out = []
    for row in ROWS:
        try:
            res = jev.decide({"text": row["text"]}, QUESTIONS)
            noul_r, depth_r = res["has_circular_reasoning"], res["reasoning_depth"]
            s0 = depth_r.answer.get("score")
            out.append({
                "rid": row["rid"], "y_circ": row["y_circ"], "d_depth": row["d_depth"],
                "noul_p": noul_r.answer.get("noul"),
                "noul_conf": noul_r.answer.get("confidence"),
                "depth_score_0based": s0,
                # 协议修正记录:真 API 0-4 标尺 → 甲方 rubric 1-5,换算写死 +1
                "depth_score": (s0 + 1) if s0 is not None else None,
                "depth_conf": depth_r.answer.get("confidence"),
                "depth_legend": depth_r.answer.get("legend"),
                "depth_probabilities": depth_r.answer.get("probabilities"),
                "noul_decision": noul_r.decision, "depth_decision": depth_r.decision,
            })
            print(f"  {row['rid']} p={out[-1]['noul_p']} s0={out[-1]['depth_score_0based']} "
                  f"s1={out[-1]['depth_score']} c={out[-1]['depth_conf']}")
        except Exception as e:
            out.append({"rid": row["rid"], "error": str(e)[:200]})
            print(f"  {row['rid']} ERROR {str(e)[:120]}")
        time.sleep(0.3)
    log_file = OUT / log_name
    if log_file.exists():
        sig = jev.sign_log()
        (OUT / f"pubkey_{model}.txt").write_text(jev.keys.pub_hex + "\n",
                                                 encoding="utf-8", newline="\n")
        v = jev.verify_log()
        print(f"  [{model}] verify: {v.detail} · sig={sig.name}")
        return out, v.detail
    print(f"  [{model}] zero logged calls — no log to sign")
    return out, "no-log"


def ece10(pairs):
    """ECE, 10 等宽桶。pairs=[(p_i, y_i, conf_i)]。"""
    n = len(pairs)
    ece = 0.0
    for k in range(10):
        lo, hi = k / 10, (k + 1) / 10
        b = [(p, y, c) for p, y, c in pairs if lo <= p < hi or (k == 9 and p == 1.0)]
        if not b:
            continue
        acc = sum(y for _, y, _ in b) / len(b)
        conf = sum(c for _, _, c in b) / len(b)
        ece += len(b) / n * abs(acc - conf)
    return ece


def metrics(rows):
    ok = [r for r in rows if "error" not in r]
    noul_ok = [r for r in ok if r["noul_p"] is not None]
    depth_ok = [r for r in ok if r["depth_score"] is not None]
    m = {"n_evaluated": len(ok), "n_errors": len(rows) - len(ok)}
    if noul_ok:
        ys = [r["y_circ"] for r in noul_ok]
        ps = [r["noul_p"] for r in noul_ok]
        cs = [r["noul_conf"] if r["noul_conf"] is not None else p
              for r, p in zip(noul_ok, ps)]
        m["noul"] = {
            "n": len(noul_ok),
            "accuracy@0.70": sum(1 for r, p in zip(noul_ok, ps)
                                 if (p >= 0.70) == bool(r["y_circ"])) / len(noul_ok),
            "brier": sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps),
            "ece10": ece10(list(zip(ps, ys, cs))),
            "per_row": {r["rid"]: {"p": r["noul_p"], "y": r["y_circ"]} for r in noul_ok},
        }
    if depth_ok:
        m["depth"] = {
            "n": len(depth_ok),
            "mae": sum(abs(r["depth_score"] - r["d_depth"]) for r in depth_ok) / len(depth_ok),
            "accuracy@3.0": sum(1 for r in depth_ok
                                if (r["depth_score"] >= 3.0) == (r["d_depth"] >= 3)) / len(depth_ok),
            "low_conf_rows": [r["rid"] for r in depth_ok
                              if r["depth_conf"] is not None and r["depth_conf"] < 0.5],
            "per_row": {r["rid"]: {"s": r["depth_score"], "d": r["d_depth"],
                                   "conf": r["depth_conf"]} for r in depth_ok},
        }
    return m


def mock_metrics():
    """mock 手写值同口径(对照列,缺答行不计)。"""
    rows = [r for r in ROWS if r["mock"]]
    ps = [r["mock"]["noul"] for r in rows]
    ys = [r["y_circ"] for r in rows]
    ss = [r["mock"]["score"] for r in rows]
    ds = [r["d_depth"] for r in rows]
    return {
        "noul": {"n": len(rows),
                 "accuracy@0.70": sum(1 for r, p in zip(rows, ps)
                                      if (p >= 0.70) == bool(r["y_circ"])) / len(rows),
                 "brier": sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps)},
        "depth": {"n": len(rows),
                  "mae": sum(abs(s - d) for s, d in zip(ss, ds)) / len(ss),
                  "accuracy@3.0": sum(1 for r, s in zip(rows, ss)
                                      if (s >= 3.0) == (r["d_depth"] >= 3)) / len(rows),
                  "low_conf_rows": [r["rid"] for r in rows if r["mock"]["confidence"] < 0.5]},
    }


def main():
    print("主批 model=jev-1.13.0(生产同构)")
    main_rows, main_verify = run_batch("jev-1.13.0", "session.jsonl")
    print("对照批 model=jev-latest(预注册可选项)")
    latest_rows, latest_verify = run_batch("jev-latest", "session_latest.jsonl")

    out = {
        "protocol": "PROTOCOL.md",
        "main_model": "jev-1.13.0", "latest_model": "jev-latest",
        "raw_main": main_rows, "raw_latest": latest_rows,
        "metrics_main": metrics(main_rows),
        "metrics_latest": metrics(latest_rows),
        "mock_handwritten": mock_metrics(),
        "verify": {"main": main_verify, "latest": latest_verify},
    }
    (OUT / "t3_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\nmetrics_main:", json.dumps(out["metrics_main"], ensure_ascii=False))
    print("mock 对照:", json.dumps(out["mock_handwritten"], ensure_ascii=False))


if __name__ == "__main__":
    main()
