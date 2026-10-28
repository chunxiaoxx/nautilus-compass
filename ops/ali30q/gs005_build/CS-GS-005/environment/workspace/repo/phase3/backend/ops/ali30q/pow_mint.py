# -*- coding: utf-8 -*-
"""PoW 铸造器 v0(阿里30q·工作量证明→NAU记账)。真实表结构适配版。

fuel_trajectories: traj_id/bounty_id/submitter/qid/context/trajectory(jsonb)/verdict/label_origin
platform_nau_ledger: agent_id/delta/reason/balance_after/linked_bounty_id(unique gate)

计价(IRT难度制):基准10 NAU,b每+0.5加5,gating门+5。验证者=compass判读层。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os

sys_path = os.path.dirname(os.path.abspath(__file__))
from sqlalchemy import create_engine, text  # noqa: E402

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production",
)
BASE_NAU = 10


def price(p: dict) -> int:
    nau = BASE_NAU
    nau += 5 * int(round((p.get("irt_b", 0) or 0) / 0.5))
    if p.get("gating"):
        nau += 5
    return nau


def pow_hash(p: dict) -> str:
    payload = json.dumps({k: p.get(k) for k in
                          ("qid", "producer", "git_hash", "ut_count", "golden_pass", "acceptor")},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def mint(engine, batch_path: str) -> None:
    batch = json.load(open(batch_path, encoding="utf-8"))
    with engine.begin() as conn:
        # balance_after: 取生产者当前余额
        for p in batch:
            h = pow_hash(p)
            tid = f"pow-{h}"
            exists = conn.execute(text(
                "SELECT 1 FROM fuel_trajectories WHERE traj_id=:t"), {"t": tid}).fetchone()
            if exists:
                print(f"  跳过(已铸): {p['qid']} {tid}")
                continue
            nau = price(p)
            conn.execute(text(
                """INSERT INTO fuel_trajectories
                   (traj_id, bounty_id, submitter, qid, context, trajectory, verdict, label_origin)
                   VALUES (:tid, :bid, :sub, :qid, :ctx, CAST(:traj AS jsonb), :ver, :lo)"""),
                {"tid": tid, "bid": f"ali30q-{p['qid']}", "sub": p["producer"], "qid": p["qid"],
                 "ctx": f"PoW凭证 UT{p['ut_count']} 金标{p['golden_pass']} 验收:{p['acceptor']}",
                 "traj": json.dumps({**p, "pow_hash": h, "nau": nau}, ensure_ascii=False),
                 "ver": "PASS", "lo": "pow-mint"})
            bal = conn.execute(text(
                "SELECT COALESCE(balance_after,0) FROM platform_nau_ledger WHERE agent_id=:a ORDER BY id DESC LIMIT 1"),
                {"a": p["producer"]}).fetchone()[0] or 0
            conn.execute(text(
                """INSERT INTO platform_nau_ledger
                   (agent_id, delta, reason, balance_after, linked_bounty_id)
                   VALUES (:a, :n, :r, :bal, :lb)"""),
                {"a": p["producer"], "n": nau,
                 "r": f"PoW {p['qid']} UT{p['ut_count']} 金标{p['golden_pass']}/{p['ut_total']} 验收:{p['acceptor']}"[:128],
                 "bal": bal + nau, "lb": f"ali30q-{p['qid']}"})
            print(f"  铸造: {p['qid']} {tid} → +{nau} NAU (balance {bal+nau})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    args = ap.parse_args()
    eng = create_engine(DATABASE_URL)
    mint(eng, args.batch)
