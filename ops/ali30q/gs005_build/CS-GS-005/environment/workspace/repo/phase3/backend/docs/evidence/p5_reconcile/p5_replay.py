#!/usr/bin/env python3
"""p5 燃料对账重放台 · platform 中立裁决工具(2026-08-25).

用法(双方交物后):
  python p5_replay.py --side v5   --indir v5/   --db "postgresql://..."
  python p5_replay.py --side flywheel --indir flywheel/ --db "postgresql://..."

输入契约(每方目录):
  raw_outputs.jsonl   每行 {"task_uid": "...", "attempt": 1, "raw_output": "<LLM 原始完整输出>"}
  extractor.py        def extract(raw_output: str) -> str   # prompt→纯代码
  params.json         {"model": "minimax-...", "temperature": .., "seed": .., "prompt": "..."}

判据 = 云 DB fde_dispatch.description 里的官方 verifier_inline(starter 判题器),
byte-exact 全等 + 防字典序作弊门。输出逐条 passed/reason + 汇总。
裁决口径(预注册,见 _OUTBOUND .../p5_reconcile.md):双方同过=V5提取器bug;双方同败=假难降级;一过一败=锁参数再跑。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import os


def load_extractor(path: str):
    spec = importlib.util.spec_from_file_location("extractor", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.extract


def replay_one(verifier_code: str, solution_code: str) -> dict:
    """注意:官方 verifier 的 argv[1] 期望的是**代码文本**(它内部再写临时文件执行),
    不是文件路径(2026-08-25 自测踩坑:传路径 → 临时文件内容=路径串 → 静默空输出)。"""
    with tempfile.TemporaryDirectory() as td:
        vp = os.path.join(td, "verifier.py")
        open(vp, "w", encoding="utf-8").write(verifier_code)
        r = subprocess.run([sys.executable, vp, solution_code], capture_output=True,
                           text=True, timeout=60, encoding="utf-8")
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"passed": False, "reason": f"verifier crash: {r.stderr[:200]}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", required=True)
    ap.add_argument("--indir", required=True)
    ap.add_argument("--db", required=True,
                    help="cloud DATABASE_URL · 只读拉 verifier")
    args = ap.parse_args()

    import psycopg2
    conn = psycopg2.connect(args.db)
    cur = conn.cursor()
    cur.execute("SELECT task_uid, description FROM fde_dispatch "
                "WHERE task_uid ILIKE '%_p5_20260824_aclass'")
    verifiers = {}
    for uid, desc in cur.fetchall():
        d = desc if isinstance(desc, dict) else json.loads(desc)
        verifiers[uid] = d["verifier_inline"]
    conn.close()

    extract = load_extractor(os.path.join(args.indir, "extractor.py"))
    n_pass = n_total = 0
    for line in open(os.path.join(args.indir, "raw_outputs.jsonl"), encoding="utf-8"):
        rec = json.loads(line)
        uid = rec["task_uid"]
        if uid not in verifiers:
            print(f"SKIP unknown task {uid}")
            continue
        code = extract(rec["raw_output"])
        verdict = replay_one(verifiers[uid], code)
        n_total += 1
        n_pass += bool(verdict.get("passed"))
        print(f"[{args.side}] {uid} attempt={rec.get('attempt')} "
              f"passed={verdict.get('passed')} reason={verdict.get('reason')}")
    print(f"== {args.side}: {n_pass}/{n_total} passed ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
