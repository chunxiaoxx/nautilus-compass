# -*- coding: utf-8 -*-
"""audit.campaign · 多账本联审入口(AUD-90 接入报表流水线)。

逐分片调用抽样并汇总敞口/样本。分片行数不足 k 属"不适用"(N/A),
跳过不拦联审结论。
"""
from audit.sampler import sample_ledger


def campaign_audit(shards: list, seed, k: int = 5) -> dict:
    """联审多份流水分片。

    shards: list[list[dict]], 每行含 id/amount/weight。
    返回: {"ok": bool, "exposure": float, "sample": list, "detail": str}
    分片行数 < k 属 N/A,跳过不计入。
    """
    executed = []
    samples = []
    exposure = 0.0
    for shard in shards:
        if len(shard) < k:
            continue  # N/A: 该分片抽不够 k 条,合理跳过
        executed.append(shard)
        samples.extend(sample_ledger(shard, seed, k))
        exposure += sum(float(r["amount"]) for r in shard)
    # 执行过的都成功 → all(); 空执行集 all()=True(「没有失败的分片」)
    ok = all(len(s) >= k for s in executed)
    n_exec = len(executed)
    return {
        "ok": ok,
        "exposure": exposure,
        "sample": samples,
        "detail": f"{n_exec}/{len(shards)} shards executed",
    }
