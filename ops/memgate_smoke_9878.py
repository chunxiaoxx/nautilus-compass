#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M5 memgate 三件套 9878 测试实例冒烟(判据先冻结):
S1 dedup_check:与既有记忆高相似文本→verdict∈{merge,gray}且hits≥1;陌生文本→unique
S2 fact_status 带出:recall 每 hit 带 fact_status 键
S3 chain_extra:recall 返回带 chain_extra 键(list 类型)
退出码 0=三测点全 PASS。"""
import json
import socket
import sys
from pathlib import Path

PORT = 9878
TOKEN = (Path.home() / ".claude" / ".cache" / "compass_daemon_token").read_text(encoding="utf-8").strip()


def req(payload: dict, timeout: float = 90.0) -> dict:
    payload["token"] = TOKEN
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(("127.0.0.1", PORT))
        s.sendall(json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n")
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.decode("utf-8"))


def main() -> int:
    results = []
    # S1a 热记忆近复述 → merge/gray(渐进 embed 下冷文件漏检已知,判据用 24h 内热条目)
    r1a = req({"action": "dedup_check", "project": "C--Users-chunx-Projects-nautilus-compass",
               "text": "sha 锚登记的 autocrlf 行尾陷阱:Windows 工作树 CRLF 与 cloud LF 是同一 blob 的两种字节,登记处 sha 与平台复验永不一致"})
    cov = r1a.get("coverage") or {}
    ok1a = (r1a.get("ok") and r1a.get("verdict") in ("merge", "gray")
            and len(r1a.get("hits") or []) >= 1 and cov.get("total", 0) > 0)
    results.append(("S1a-hot-dup-similar", ok1a,
                    f"verdict={r1a.get('verdict')} top={(r1a.get('hits') or [{}])[0].get('score')} coverage={cov.get('embedded')}/{cov.get('total')}"))
    # S1b 陌生文本 → unique
    r1b = req({"action": "dedup_check", "project": "C--Users-chunx-Projects-nautilus-compass",
               "text": "量子色动力学格点模拟的规范不变性费曼图重整化群流反常维数"})
    ok1b = r1b.get("ok") and r1b.get("verdict") == "unique"
    results.append(("S1b-novel-unique", ok1b, f"verdict={r1b.get('verdict')}"))
    # S2+S3 recall(结果键=recall,同 J4 gate 口径)
    r2 = req({"action": "recall", "project": "C--Users-chunx-Projects-nautilus-compass",
              "query": "G1 判读 rollout 主判据地板", "top_k": 5})
    hits = r2.get("recall") or []
    ok2 = bool(hits) and all("fact_status" in h for h in hits)
    results.append(("S2-fact_status-key", ok2, f"n={len(hits)} sample_fact_status={ [h.get('fact_status') for h in hits[:3]] }"))
    has_chain = "chain_extra" in r2
    ok3 = has_chain and isinstance(r2.get("chain_extra"), list)
    n_chain = len(r2.get("chain_extra") or [])
    results.append(("S3-chain_extra", ok3, f"present={has_chain} len={n_chain}"))

    all_ok = True
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} · {detail}")
        all_ok = all_ok and ok
    print("SMOKE:", "GREEN" if all_ok else "RED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
