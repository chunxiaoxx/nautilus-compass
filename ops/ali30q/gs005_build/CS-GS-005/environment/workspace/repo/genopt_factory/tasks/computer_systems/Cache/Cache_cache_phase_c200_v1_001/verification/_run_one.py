"""Worker: load candidate + instance, run run_cache, write result.json."""

import argparse
import importlib.util
import json
import os
import sys


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

    result = mod.run_cache(inst)
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump({"misses": int(result.get("misses", 0)),
                   "miss_rate": float(result.get("miss_rate", 0.0))}, f,
                  ensure_ascii=False)


if __name__ == "__main__":
    main()