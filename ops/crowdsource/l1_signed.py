# -*- coding: utf-8 -*-
"""L1 机审签名壳:机审结果 → HMAC 签名报告(可验证工件,接 /assay/gates 密钥体系)。
与 l1_machine_check.py 配套;签名密钥复用 ~/.claude/.cache/assay_gates_signing.key。
用法:python l1_signed.py <order.json> <delivery_dir> [out.json]
"""
import hashlib, hmac, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from l1_machine_check import l1_check
import os

KEY_FILE = os.path.expanduser("~/.claude/.cache/assay_gates_signing.key")


def sign(payload: dict) -> str:
    key = open(KEY_FILE, "rb").read()
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hmac.new(key, body.encode(), hashlib.sha256).hexdigest()


def main():
    order = json.load(open(sys.argv[1], encoding="utf-8"))
    r = l1_check(order, Path(sys.argv[2]))
    # 单文冻结证明:order 全文哈希(与接单快照哈希比对=判据未改的物证)
    order_sha = hashlib.sha256(
        json.dumps(order, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    report = {"l1": r, "order_sha256": order_sha, "ts": time.time()}
    report["signature"] = sign({"l1": r, "order_sha256": order_sha, "ts": report["ts"]})
    out = sys.argv[3] if len(sys.argv) > 3 else "l1_report.json"
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"verdict={r['verdict']} | order_sha={order_sha[:16]}… | signed → {out}")


if __name__ == "__main__":
    main()
