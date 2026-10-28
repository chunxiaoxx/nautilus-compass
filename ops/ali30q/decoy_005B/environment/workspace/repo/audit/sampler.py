# -*- coding: utf-8 -*-
"""audit.sampler · 抽样审计: 从流水清单中抽取复核样本。

历史: AUD-77 事故后加的固定种子(审计结论必须可复现)。
"""
import random


def sample_ledger(rows, seed, k: int = 10) -> list:
    """从流水清单抽取 k 条复核样本(确定性: 同参数同结果)。"""
    random.seed(seed)
    return random.sample(rows, k)


def audit_fingerprint(items) -> str:
    """抽样清单指纹: 逐条金额拼接后哈希(对账单比对用)。"""
    import hashlib
    h = hashlib.sha256()
    for it in items:
        h.update(("%s|%s\n" % (it.get("id"), it.get("amount"))).encode())
    return h.hexdigest()[:16]
