"""Worker: load candidate + instance, run find_path, write result.json."""

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

    result = mod.find_path(inst)
    raw_cost = result.get("cost", 0)
    try:
        if raw_cost == float("inf") or raw_cost is None:
            cost = 0
        else:
            cost = int(raw_cost)
    except (OverflowError, ValueError, TypeError):
        cost = 0
    out_path = os.path.abspath("result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"path": list(result.get("path", [])),
                   "cost": cost,
                   "valid": bool(result.get("valid", False))}, f, ensure_ascii=False)


if __name__ == "__main__":
    main()