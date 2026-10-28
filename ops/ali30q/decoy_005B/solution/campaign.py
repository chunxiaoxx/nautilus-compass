# -*- coding: utf-8 -*-
"""audit.campaign · 修复版(AUD-90)。

§4 切分合并原则贯穿联审层: 分片是同一份流水的划分,短分片不是
N/A——金额必须并入全局敞口,行必须进入全局抽样池。空联审
(零行)不得报 ok=True(空集≠审过)。抽样在整数权重域上对并集
精确进行一次,样本长度 = min(k, 并集行数),与分片切法无关。
"""
import math
import random


def _risk_sample(rows, seed, k: int) -> list:
    """§5: 先按 id 规范化序剥离入账/分片顺序,再整数权重域无放回抽样。"""
    if not rows:
        return []
    rng = random.Random(seed)
    pool = sorted(rows, key=lambda r: str(r["id"]))
    k = min(k, len(pool))
    picked = []
    while len(picked) < k and pool:
        weights = [max(0, int(r.get("weight", 0))) for r in pool]
        total = sum(weights)
        if total <= 0:
            picked.append(pool.pop(0))
            continue
        x = rng.randrange(total)
        acc = 0
        for i, w in enumerate(weights):
            acc += w
            if x < acc:
                picked.append(pool.pop(i))
                break
    return picked


def campaign_audit(shards: list, seed, k: int = 5) -> dict:
    """联审多份流水分片。

    verified/ok=True 当且仅当并集非空且已对并集完成一次审计。
    短分片(len < k)不是跳过理由——§4 要求切分后合并结论与整单一致。
    """
    union = []
    for shard in shards:
        union.extend(shard)
    exposure = math.fsum(float(r["amount"]) for r in union) if union else 0.0
    sample = _risk_sample(union, seed, k)
    ok = bool(union)
    skipped = [i for i, s in enumerate(shards) if len(s) < k]
    skip_note = f" · short:{','.join(map(str, skipped))}" if skipped else ""
    return {
        "ok": ok,
        "exposure": exposure,
        "sample": sample,
        "detail": f"{len(shards) - len(skipped)}/{len(shards)} shards in union{skip_note}",
    }
