"""One-shot patcher · adds per-question JSONL persistence to evermembench_bge.py.

Run on T4: python3 patch_evermembench_persist.py
Idempotent — checks if patch already applied.
"""
import sys
from pathlib import Path

TARGET = Path("/home/ubuntu/evermembench_bge.py")
BAK = Path("/home/ubuntu/evermembench_bge.py.bak.20260507")
OUT_PATH = "/home/ubuntu/em_bge_v2_per_question.jsonl"


def main() -> int:
    if not TARGET.is_file():
        print(f"ERR target not found: {TARGET}")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if "JSONL_OUT.write" in src:
        print("already patched")
        return 0

    if not BAK.is_file():
        BAK.write_text(src, encoding="utf-8")
        print(f"backup -> {BAK}")

    anchor_loop = (
        '            ok = "CORRECT" in verdict and "INCORRECT" not in verdict\n'
        "            if ok:\n"
        "                n_correct += 1\n"
        "            n_total += 1\n"
    )
    replacement_loop = (
        '            ok = "CORRECT" in verdict and "INCORRECT" not in verdict\n'
        "            recall_hit = bool(retrieved_keys and any(rk_ in refs for rk_ in retrieved_keys))\n"
        "            JSONL_OUT.write(json.dumps({\n"
        '                "topic": TOPIC,\n'
        '                "qa_id": qa.get("id", ""),\n'
        '                "Q": Q,\n'
        '                "gold": A,\n'
        '                "pred": pred,\n'
        '                "verdict_raw": verdict,\n'
        '                "ok": ok,\n'
        '                "recall_hit": recall_hit,\n'
        '                "n_retrieved": len(retrieved_keys),\n'
        '            }, ensure_ascii=False) + "\\n")\n'
        "            JSONL_OUT.flush()\n"
        "            if ok:\n"
        "                n_correct += 1\n"
        "            n_total += 1\n"
    )

    if anchor_loop not in src:
        print("ERR loop anchor not found · runner has changed")
        return 2
    src = src.replace(anchor_loop, replacement_loop, 1)

    anchor_main = "def main():"
    replacement_main = (
        f'JSONL_PATH = "{OUT_PATH}"\n'
        'JSONL_OUT = open(JSONL_PATH, "w", encoding="utf-8", buffering=1)\n'
        "\n"
        "\n"
        "def main():"
    )
    if anchor_main not in src:
        print("ERR main anchor not found")
        return 3
    src = src.replace(anchor_main, replacement_main, 1)

    TARGET.write_text(src, encoding="utf-8")
    print("patched")

    import ast
    try:
        ast.parse(src)
        print("syntax OK")
    except SyntaxError as e:
        print(f"SYNTAX FAIL: {e}")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
