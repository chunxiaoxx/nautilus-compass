#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""决策锚定上链(创世 Blockchain 模块兑现·U33④·2026-10-02 夜)。

把组织决策数据集按日锚定到 Base 链:当日全部决策行逐行 SHA256 → 拼接得 Merkle 根
→ 若 BLOCKCHAIN_PRIVATE_KEY 在 .env.blockchain 则发 Base Sepolia tx(data=根)回填 tx_hash;
无 key 则 pending_key 状态(晨间呈用户提供私钥=用户产权,或用现有结算钱包发)。

幂等:按 anchor_date 唯一(已锚定日跳过,tx_hash 未填可重试)。
用法: python ops/decision_anchor.py            # 锚定昨日(或--date)
      python ops/decision_anchor.py --backfill # 补齐全部未锚定日
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.database import SessionLocal  # noqa: E402
from sqlalchemy import text  # noqa: E402

DS = Path(__file__).resolve().parents[1] / "docs" / "evidence" / "org-os" / "decision_dataset.jsonl"
ENV_BC = Path(__file__).resolve().parents[1] / ".env.blockchain"


def _env() -> dict:
    env = {}
    for p in (ENV_BC, Path(__file__).resolve().parents[1] / ".env.blockchain.local"):
        if p.exists():
            for ln in p.read_text().splitlines():
                if "=" in ln and not ln.startswith("#"):
                    k, v = ln.split("=", 1)
                    env[k.strip()] = v.strip().strip('"')
    return env


def merkle_root(rows: list[dict]) -> tuple[str, int]:
    """逐行规范哈希→排序拼接→根哈希(简化 Merkle:排序保证确定性,空行安全)。"""
    hs = sorted(hashlib.sha256(
        json.dumps(r, ensure_ascii=False, sort_keys=True).encode()).hexdigest() for r in rows)
    if not hs:
        return hashlib.sha256(b"empty-day").hexdigest(), 0
    return hashlib.sha256("".join(hs).encode()).hexdigest(), len(rows)


def ensure_table(s) -> None:
    s.execute(text("""
        CREATE TABLE IF NOT EXISTS chain_anchors (
            id SERIAL PRIMARY KEY,
            anchor_date DATE NOT NULL UNIQUE,
            digest_count INT NOT NULL,
            merkle_root TEXT NOT NULL,
            tx_hash TEXT,
            chain TEXT DEFAULT 'base-sepolia',
            status TEXT NOT NULL DEFAULT 'pending_key',
            created_at TIMESTAMPTZ DEFAULT now())
    """))
    s.commit()


def anchor_day(s, day: str) -> dict | None:
    rows = []
    if DS.exists():
        for ln in DS.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
                if str(r.get("ts", ""))[:10] == day:
                    rows.append(r)
            except Exception:  # noqa: BLE001
                continue
    root, n = merkle_root(rows)
    exists = s.execute(text(
        "SELECT id, merkle_root, tx_hash, status FROM chain_anchors WHERE anchor_date=:d"),
        {"d": day}).fetchone()
    if exists and exists[3] == "anchored":
        return {"day": day, "skip": "already anchored", "root": exists[1]}
    if exists and exists[2]:  # 有 tx 但状态没更新
        s.execute(text("UPDATE chain_anchors SET status='anchored' WHERE id=:i"), {"i": exists[0]})
        s.commit()
    if not exists:
        s.execute(text(
            "INSERT INTO chain_anchors (anchor_date, digest_count, merkle_root, status) "
            "VALUES (:d, :n, :r, 'pending_key')"),
            {"d": day, "n": n, "r": root})
        s.commit()
    else:
        s.execute(text("UPDATE chain_anchors SET digest_count=:n, merkle_root=:r WHERE id=:i"),
                  {"n": n, "r": root, "i": exists[0]})
        s.commit()
    return {"day": day, "rows": n, "merkle_root": root, "status": "pending_key"}


def send_tx(root: str, env: dict) -> str | None:
    """发 Base Sepolia tx(data=0x+root),返回 tx_hash。失败返回 None(不抛)。"""
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(env.get("BASE_SEPOLIA_RPC", "https://sepolia.base.org")))
        acct = w3.eth.account.from_key(env["BLOCKCHAIN_PRIVATE_KEY"])
        nonce = w3.eth.get_transaction_count(acct.address)
        tx = {
            "nonce": nonce, "gas": 30000, "maxFeePerGas": w3.to_wei(0.15, "gwei"),
            "maxPriorityFeePerGas": w3.to_wei(0.01, "gwei"), "chainId": 84532,
            "to": acct.address, "value": 0, "data": "0x" + root,
            "type": 2,
        }
        signed = acct.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signed.raw_transaction).hex()
        w3.eth.wait_for_transaction_receipt(h, timeout=90)
        return h
    except Exception as e:  # noqa: BLE001
        print(f"  tx fail: {str(e)[:80]}")
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--backfill", action="store_true")
    a = ap.parse_args()
    env = _env()
    has_key = bool(env.get("BLOCKCHAIN_PRIVATE_KEY"))
    s = SessionLocal()
    ensure_table(s)
    days = [a.date] if a.date else [str((datetime.now() - timedelta(days=1)).date())]
    if a.backfill and DS.exists():
        seen = {str(r.get("ts", ""))[:10] for ln in DS.read_text(encoding="utf-8").splitlines()
                if ln.strip() for r in [json.loads(ln)]}
        done = {r[0] for r in s.execute(text("SELECT anchor_date FROM chain_anchors WHERE status='anchored'")).fetchall()}
        days = sorted(seen - done)
    for d in days:
        r = anchor_day(s, d)
        if not r or r.get("skip"):
            print(f"{d}: {r}")
            continue
        if has_key:
            tx = send_tx(r["merkle_root"], env)
            if tx:
                s.execute(text(
                    "UPDATE chain_anchors SET tx_hash=:t, status='anchored' WHERE anchor_date=:d"),
                    {"t": tx, "d": d})
                s.commit()
                r.update(status="anchored", tx=tx)
        print(f"{d}: rows={r['rows']} root={r['merkle_root'][:16]}… status={r['status']}")
    total = s.execute(text("SELECT count(*), count(tx_hash) FROM chain_anchors")).fetchone()
    print(f"anchors total={total[0]} on-chain={total[1]} (key={'present' if has_key else 'ABSENT→pending'})")
    s.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
