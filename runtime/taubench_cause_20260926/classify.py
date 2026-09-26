# -*- coding: utf-8 -*-
"""τ-bench R1 29 失败题机械判因(2026-09-26 · compass 判分 owner 首件).

位点分类(1053 函口径):工具选择/参数错/政策违反/多约束丢失/漏动作/
被模拟器带偏/评测器嫌疑。纯机械:序列对齐+参数 diff+tool 响应 error 检测。
输出 cause_table.json + 摘要。用法:python classify.py
"""
import ast
import json
import re
from pathlib import Path

SRC = Path(r"C:/Users/chunx/nautilus-v5/deliverables/taubench_r1_fail_traces")


def load(task_file):
    d = json.loads((SRC / task_file).read_text(encoding="utf-8"))[0]
    info = ast.literal_eval(d["info"]) if isinstance(d["info"], str) else d["info"]
    traj = ast.literal_eval(d["traj"]) if isinstance(d["traj"], str) else d["traj"]
    return info, traj, d.get("reward")


def writes(seq):
    """写动作=有副作用的调用(env 会改状态)。τ-bench retail 写集。"""
    W = {"modify_pending_order_items", "modify_pending_order_address",
         "cancel_pending_order", "return_delivered_order_items",
         "exchange_delivered_order_items"}
    return [(n, a) for n, a in seq if n in W]


def norm_args(a):
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            return a
    if isinstance(a, dict):
        return {k: json.dumps(v, sort_keys=True) for k, v in a.items()}
    return a


def classify(item):
    info, traj, reward = load(item["file"])
    gold_seq = [(a["name"], norm_args(a.get("kwargs") or a.get("arguments")))
                for a in info["task"]["actions"]]
    agent_seq = []
    tool_resp = []
    for m in traj:
        for tc in (m.get("tool_calls") or []):
            f = tc["function"]
            agent_seq.append((f["name"], norm_args(f["arguments"])))
        if m.get("role") == "tool":
            tool_resp.append(m.get("content") or "")
    gw, aw = writes(gold_seq), writes(agent_seq)

    def key(x):
        return (x[0], tuple(sorted((x[1] or {}).items())) if isinstance(x[1], dict) else str(x[1]))

    gset, aset = {key(x) for x in gw}, {key(x) for x in aw}
    missing = gset - aset
    extra = aset - gset
    errs = [r[:120] for r in tool_resp if "error" in r.lower()[:80]]

    # 位点判定(机械可判优先)
    gnames_miss = None
    miss_names = set()
    if missing and extra:
        m_names = {x[0] for x in gw if key(x) in missing}
        e_names = {x[0] for x in aw if key(x) in extra}
        if m_names & e_names:
            # 同名工具 miss+extra 成对 = 参数值差异,非漏/多
            cause = "参数错(值级)"
        else:
            cause = "混合(漏写+多写)"
    elif missing:
        cause = "漏动作(写缺失)"
    elif extra:
        gnames = {n for n, _ in gw}
        if {n for n, _ in writes(agent_seq)} - gnames:
            cause = "多写(工具选择错)"
        else:
            cause = "参数错(写集合不等,同名工具)"
    else:
        # 写集合完全相等 → 查执行层
        if errs:
            cause = "执行失败(参数同但 env 拒)"
        else:
            cause = "评测器嫌疑(写全同+无报错)"
    # 政策违反启发:payment_method 不在 gold 出现的集合里
    policy = ""
    gm = {v for n, a in gw if isinstance(a, dict)
          for k, v in a.items() if "payment" in k}
    am = {v for n, a in aw if isinstance(a, dict)
          for k, v in a.items() if "payment" in k}
    if am - gm and am:
        policy = f"支付方式异({sorted(am - gm)})"
    return {"task_id": item["task_id"], "prelim": item["prelim_type"],
            "cause": cause, "policy_hint": policy,
            "n_gold_writes": len(gw), "n_agent_writes": len(aw),
            "tool_errors": len(errs), "reward": reward}


def main():
    idx = json.loads((SRC / "index.json").read_text(encoding="utf-8"))
    items = idx if isinstance(idx, list) else idx.get("items") or idx.get("traces")
    rows = [classify(i) for i in items]
    out = Path(__file__).parent / "cause_table.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    from collections import Counter
    c = Counter(r["cause"] for r in rows)
    print(f"n={len(rows)}")
    for k, v in c.most_common():
        print(f"  {v:2}  {k}")
    print("\n评测器嫌疑题:", [r["task_id"] for r in rows
                               if "评测器嫌疑" in r["cause"]])
    print("支付异题:", [(r["task_id"], r["policy_hint"]) for r in rows
                          if r["policy_hint"]][:8])


if __name__ == "__main__":
    main()
