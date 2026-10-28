"""Worker: load candidate + instance, run qaoa_maxcut, write result.json."""

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

    result = mod.qaoa_maxcut(inst)
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump({"bitstring": list(result.get("bitstring", [])),
                   "cut_size": int(result.get("cut_size", 0))}, f, ensure_ascii=False)


if __name__ == "__main__":
    main()