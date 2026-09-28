# -*- coding: utf-8 -*-
"""L1 硬机审(V2 众包验收流水线第 4 步 · 承 V2_CROWDSOURCE_ACCEPTANCE)。

用法:python l1_machine_check.py <order.json> <delivery_dir>
- order.json=挂单正本(判据预注册冻结件,含 l1_schema/要求清单)
- delivery_dir=交付目录(登记过的交付物)

输出:逐项机审结果+返工提示(首次返工权用)+JSON 报告(带哈希可入回执)。
设计律:L1 只验客观项(格式/数量/哈希/活链),零主观;主观= L2 样例锚,
人的判断不进本程序。
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def check_url_alive(url: str, timeout=15) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "assay-l1/1.0"})
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status < 400
    except Exception:
        return False


def l1_check(order: dict, delivery_dir: Path) -> dict:
    results, hard_fail = [], 0
    files = sorted([p for p in delivery_dir.iterdir() if p.is_file()])
    manifest_files = [f for f in files if f.suffix in (".json", ".jsonl", ".csv")]

    # 1) 数量门
    req_n = order.get("l1", {}).get("min_files")
    if req_n is not None:
        ok = len(files) >= req_n
        results.append(("count", ok, f"{len(files)}/{req_n}"))
        hard_fail += 0 if ok else 1

    # 2) 格式门:交付 JSON 必须满足单内 schema(轻量校验:必填键+类型)
    schema = order.get("l1", {}).get("schema", {})
    bad_rows = 0
    rows = 0
    for f in manifest_files:
        try:
            if f.suffix == ".jsonl":
                items = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
            else:
                items = json.load(open(f, encoding="utf-8"))
                items = items if isinstance(items, list) else [items]
        except Exception:
            results.append(("parse", False, f"{f.name} 解析失败"))
            hard_fail += 1
            continue
        for it in items:
            rows += 1
            for k, typ in schema.items():
                v = it.get(k)
                if v is None or not isinstance(v, {"str": str, "num": (int, float),
                                                   "bool": bool, "list": list}.get(typ, object)):
                    bad_rows += 1
                    break
    if schema:
        ok = bad_rows == 0 and rows >= order.get("l1", {}).get("min_rows", 1)
        results.append(("schema", ok, f"rows={rows} bad={bad_rows}"))
        hard_fail += 0 if ok else 1

    # 3) 哈希门:交付登记表(若随交付提交)自洽——防调包
    reg = delivery_dir / "_delivery_manifest.json"
    if reg.exists():
        m = json.load(open(reg, encoding="utf-8"))
        mism = [e["file"] for e in m.get("files", [])
                if sha256_file(delivery_dir / e["file"]) != e.get("sha256")]
        ok = not mism
        results.append(("hash", ok, "自洽" if ok else f"不匹配:{mism}"))
        hard_fail += 0 if ok else 1

    # 4) 活链门:登记表里的 URL 可达
    urls = [e.get("url") for e in (json.load(open(reg, encoding="utf-8"))
                                   .get("files", [])) if e.get("url")] if reg.exists() \
        else order.get("l1", {}).get("verify_urls", [])
    dead = [u for u in urls if not check_url_alive(u)]
    if urls:
        results.append(("urls", not dead, f"{len(urls)-len(dead)}/{len(urls)} 活"))
        hard_fail += 0 if not dead else 1

    verdict = "pass" if hard_fail == 0 else "rework"
    return {
        "gate": "L1", "verdict": verdict,
        "items": [{"check": n, "ok": ok, "detail": d} for n, ok, d in results],
        "rework_hints": [f"{n}: {d}" for n, ok, d in results if not ok],
        "manifest_sha256": sha256_file(delivery_dir / files[0]) if files else "",
    }


if __name__ == "__main__":
    order = json.load(open(sys.argv[1], encoding="utf-8"))
    d = Path(sys.argv[2])
    print(json.dumps(l1_check(order, d), ensure_ascii=False, indent=1))
