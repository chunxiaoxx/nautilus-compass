# -*- coding: utf-8 -*-
"""422 定位探针:一次一变量。a=域3已知好格式,逐项加回。"""
from pathlib import Path
from jev_trust import TrustedJev

KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"
api_key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]

TXT = "Let f = lambda x: x**2. Then f'(x) = 2x."
NOUL_Q = "Does this reasoning contain circular reasoning or assume the conclusion?"
DEPTH_INSTR = "Rate the mathematical and logical rigor of this explanation."

CASES = [
    ("a: noul 无 criteria, jev-latest",
     {"qid": {"type": "noul", "instructions": NOUL_Q}}, "jev-latest"),
    ("b: noul + criteria dict, jev-latest",
     {"qid": {"type": "noul", "instructions": NOUL_Q,
              "criteria": {"true": "t", "false": "f"}}}, "jev-latest"),
    ("c: score + criteria dict, jev-latest",
     {"qid": {"type": "score", "instructions": DEPTH_INSTR,
              "criteria": {"1": "a", "5": "e"}}}, "jev-latest"),
    ("d: noul 无 criteria, jev-1.13.0",
     {"qid": {"type": "noul", "instructions": NOUL_Q}}, "jev-1.13.0"),
]

for name, qs, model in CASES:
    try:
        jev = TrustedJev(api_key=api_key, domain="probe-format-t3", model=model)
        r = jev.decide({"text": TXT}, qs)["qid"]
        print(f"[OK]   {name} -> answer={r.answer}")
    except Exception as e:
        print(f"[FAIL] {name} -> {str(e)[:150]}")
