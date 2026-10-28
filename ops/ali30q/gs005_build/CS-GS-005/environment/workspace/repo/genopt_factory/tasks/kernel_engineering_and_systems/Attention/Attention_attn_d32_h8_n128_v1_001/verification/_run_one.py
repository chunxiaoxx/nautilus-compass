"""Worker: load candidate + instance, run attention_forward, write result.json.

Used by verification/evaluate.py to isolate one candidate run from the scoring
loop. Measures wall-clock elapsed_s around the forward call.
"""

import argparse
import importlib.util
import json
import os
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--instance", required=True)
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location("candidate", args.candidate)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with open(args.instance, encoding="utf-8") as f:
        inst = json.load(f)

    t0 = time.monotonic()
    result = mod.attention_forward(inst)
    elapsed = time.monotonic() - t0

    # Always set elapsed_s even if candidate didn't.
    result["elapsed_s"] = round(elapsed, 4)

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump({"O": result.get("O", []),
                   "elapsed_s": result["elapsed_s"]}, f, ensure_ascii=False)


if __name__ == "__main__":
    main()