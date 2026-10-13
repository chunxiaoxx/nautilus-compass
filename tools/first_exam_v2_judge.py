#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""首考评测骨架(11154 拍甲 · 判据 v2.0 三门 · 30 题单轮)。

待 v5 回三项材料(判据档 v2.0 全文路径/卷面抽取规则/token 坐标)后填参数执行:
  python tools/first_exam_v2_judge.py --paper <卷面.json> --token-env <ENV名> [--base <8001地址>]

三门(判据 v2.0,sha16=53f81a219e8914f1):
  ①空回包率 <10%  ②JSON 合法率 ≥80%  ③延迟窗 ≤240s/题
输出:首考判定表(逐题+三门+归档 JSON)
"""
import argparse
import json
import os
import time
import urllib.request
from pathlib import Path


def call_server(base, token, system_prompt, user_prompt, timeout=240):
    """单题调用 8001 服务端(system+user 单轮,#11148 口径)。"""
    payload = json.dumps({"model": "default",
                          "messages": [{"role": "system", "content": system_prompt},
                                       {"role": "user", "content": user_prompt}],
                          "temperature": 0}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=payload, method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        lat = time.time() - t0
        content = (r.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return {"lat": round(lat, 1), "empty": not content.strip(), "content": content}
    except Exception as e:
        return {"lat": round(time.time() - t0, 1), "empty": True, "content": "",
                "err": f"{type(e).__name__}: {e}"[:80]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True, help="卷面 JSON(30 题,system/user 字段)")
    ap.add_argument("--base", default="http://127.0.0.1:8001/v1")
    ap.add_argument("--token-env", required=True)
    ap.add_argument("--out", default="runtime/first_exam_v2_verdict.json")
    a = ap.parse_args()
    token = os.environ.get(a.token_env)
    assert token, f"env {a.token_env} empty"

    paper = json.loads(Path(a.paper).read_text(encoding="utf-8"))
    items = paper if isinstance(paper, list) else paper.get("items", paper.get("questions"))
    assert len(items) == 30, f"expect 30 items, got {len(items)}"

    rows = []
    for i, it in enumerate(items):
        res = call_server(a.base, token, it.get("system", ""), it.get("user", it.get("content", "")))
        res["i"] = i + 1
        rows.append(res)
        print(f"[{i+1}/30] lat={res['lat']}s empty={res['empty']}", flush=True)

    empty_rate = sum(1 for r in rows if r["empty"]) / len(rows)
    json_ok = sum(1 for r in rows if not r["empty"]
                  and _is_json(r["content"])) / len(rows)
    lat_max = max(r["lat"] for r in rows)
    gates = {
        "G1_empty_rate_lt_10pct": {"value": round(empty_rate*100, 1), "pass": empty_rate < 0.10},
        "G2_json_valid_ge_80pct": {"value": round(json_ok*100, 1), "pass": json_ok >= 0.80},
        "G3_latency_le_240s": {"value": lat_max, "pass": lat_max <= 240},
    }
    verdict = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
               "criteria_sha16": "53f81a219e8914f1", "n": len(rows),
               "gates": gates,
               "verdict": "FIRST_EXAM_PASS" if all(g["pass"] for g in gates.values()) else "FIRST_EXAM_FAIL",
               "rows": rows}
    Path(a.out).write_text(json.dumps(verdict, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in verdict.items() if k != "rows"}, ensure_ascii=False, indent=1))


def _is_json(s):
    try:
        json.loads(s)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()
