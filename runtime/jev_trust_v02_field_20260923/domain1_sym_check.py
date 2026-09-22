# -*- coding: utf-8 -*-
"""特异度对照:域 1 dogfood zerodiv 20 题(模型会做,域1 C=0.953)双极性自检。
预期低冲突率——自检在可信域不乱杀。追加协议:同 PROTOCOL 口径。"""
import json
import sys
import time
from pathlib import Path

from jev_trust import TrustedJev

OUT = Path(__file__).parent
D1 = Path(__file__).parent.parent / "jev_trust_dogfood_20260922"
KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"

NORM = ("If this exact Python call were executed, would it raise an exception? "
        "Answer strictly from Python semantics.")
FLIP = ("If this exact Python call were executed, would it complete without "
        "raising any exception? Answer strictly from Python semantics.")


def main():
    ds = json.loads((D1 / "decision_set.json").read_text(encoding="utf-8"))
    rows = [d for d in ds if d["pattern"] == "zerodiv"]
    assert len(rows) == 20
    api_key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]
    jev = TrustedJev(api_key=api_key, domain="bipolarity-easy-control",
                     log_path=str(OUT / "domain1_sym.jsonl"))
    out = []
    for n, d in enumerate(rows):
        qid = "e1-" + d["qid"]
        try:
            r = jev.decide_symmetric(d["state"], {qid: {
                "question": {"type": "noul", "instructions": NORM},
                "opposite": {"type": "noul", "instructions": FLIP}}})[qid]
            out.append({"qid": qid, "truth_raises": d["truth"],
                        "conflict": not r.polarity_consistent,
                        "sym_says_raise": r.decision == "yes"})
        except Exception as e:
            out.append({"qid": qid, "error": str(e)[:120]})
        time.sleep(0.25)
    sig = jev.sign_log()
    (OUT / "pubkey_d1.txt").write_text(jev.keys.pub_hex + "\n", encoding="utf-8", newline="\n")
    (OUT / "domain1_sym_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    ok = [r for r in out if "error" not in r]
    conf = sum(1 for r in ok if r["conflict"])
    usable = [r for r in ok if not r["conflict"]]
    correct = sum(1 for r in usable if r["sym_says_raise"] == (r["truth_raises"] == 1))
    print(f"easy-control: n={len(ok)} conflicts={conf} ({conf/max(1,len(ok))*100:.0f}%) "
          f"| consistent acc={correct}/{len(usable)}")


if __name__ == "__main__":
    sys.exit(main())
