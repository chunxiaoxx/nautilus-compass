# -*- coding: utf-8 -*-
"""Assay BC1 生成器 — 30 题,seed=20260927(PROTOCOL.md 判据 1)。

四维 × 参数化 × 机器可判:每题产 {qid, dim, type, prompt, inputs,
expected, check{kind,spec}, criteria_ref, public}(18/12 切分判据 4)。
脱敏:角色代号 A-E(判据 3)。判分器=verify_bc1.py(独立可跑,判据 2)。
"""
import json
import random
from pathlib import Path

SEED = 20260927
SPLIT_SEED = 2026092751
OUT = Path(__file__).parent
rng = random.Random(SEED)

DAYS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]
ROLES = ["A", "B", "C", "D", "E"]


# ── DIM1 跨框状态一致(7)────────────────────────────────────────

def gen_mailbox_timeline(n_days=5, n_events=14):
    """程序生成脱敏函件时间线:sent/ack/reply/promise/deadline 事件。"""
    events = []
    for i in range(n_events):
        day = rng.choice(DAYS[:n_days])
        r_from, r_to = rng.sample(ROLES, 2)
        kind = rng.choice(["sent", "ack", "reply", "promise"])
        ev = {"day": day, "from": r_from, "to": r_to, "kind": kind,
              "id": f"M{i:03d}"}
        if kind == "promise":
            ev["promise_day"] = rng.choice(DAYS)
        events.append(ev)
    return events


def status_of(events, role, day):
    """期望状态推导(真值):承诺中/已回/待办。"""
    idx = DAYS.index(day)
    due, replied, pending = [], [], []
    seen = set()
    for ev in events:
        if DAYS.index(ev["day"]) > idx or ev["id"] in seen:
            continue
        seen.add(ev["id"])
        if ev["kind"] == "promise" and ev["to"] == role:
            if DAYS.index(ev["promise_day"]) <= idx:
                due.append(ev["id"])
        if ev["kind"] == "reply" and ev["from"] == role:
            replied.append(ev["id"])
        if ev["kind"] == "sent" and ev["to"] == role:
            pending.append(ev["id"])
    pending = [p for p in pending if p not in replied]
    return {"due_promises": sorted(due), "replied": sorted(replied),
            "unanswered": sorted(pending)}


def dim1():
    items = []
    # T1.1 函件账本题 ×3
    for i in range(3):
        evs = gen_mailbox_timeline()
        role = rng.choice(ROLES)
        day = rng.choice(DAYS)
        expected = status_of(evs, role, day)
        items.append({
            "qid": f"T11-{i}", "dim": "DIM1", "type": "mailbox-status",
            "prompt": f"Given the mail-log below, what is role {role}'s exact "
                      f"status at end of {day}? Answer with the JSON object "
                      f"{{\"due_promises\":[...],\"replied\":[...],\"unanswered\":[...]}}.",
            "inputs": {"events": evs, "role": role, "day": day},
            "expected": expected,
            "check": {"kind": "json_map_equal",
                      "spec": {"target": "answer_json"}},
            "criteria_ref": "verdict-recomputability-v1",
            "public": None})
    # T1.2 冲突检出题 ×2(埋声明 vs 回执数字矛盾)
    for i in range(2):
        claimed, actual = rng.randint(10, 90), rng.randint(10, 90)
        while claimed == actual:
            actual = rng.randint(10, 90)
        log = [
            {"day": "D1", "from": "A", "kind": "claim",
             "text": f"B processed {claimed} requests last week."},
            {"day": "D2", "from": "B", "kind": "receipt",
             "raw": [rng.randint(0, 9) for _ in range(actual)]},
            {"day": "D3", "from": "C", "kind": "claim",
             "text": f"A acknowledged all of B's {actual + rng.randint(1, 5)} requests."},
        ]
        items.append({
            "qid": f"T12-{i}", "dim": "DIM1", "type": "conflict-detect",
            "prompt": "The log contains claims that conflict with raw evidence. "
                      "Identify every conflicting pair as {\"claim_day\":\"..\","
                      "\"evidence_day\":\"..\"} in a JSON list. If none, answer [].",
            "inputs": {"log": log},
            "expected": [{"claim_day": "D1", "evidence_day": "D2"}],
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "judge-systematic-inconsistency-v1",
            "public": None})
    # T1.3 派生一致题 ×2(A 报的数字能否由 B 的原始行推出)
    for i in range(2):
        rows = [{"date": f"D{k}", "ok": rng.randint(0, 4), "fail": rng.randint(0, 4)}
                for k in range(1, 7)]
        # A claims: success rate = total_ok / (total_ok+total_fail) rounded
        tot_ok = sum(r["ok"] for r in rows)
        tot_all = tot_ok + sum(r["fail"] for r in rows)
        true_rate = round(tot_ok / tot_all, 2)
        claimed_rate = round(min(1.0, true_rate + rng.choice([-0.15, 0.1, 0.2])), 2)
        if claimed_rate == true_rate:
            claimed_rate = round(true_rate + 0.1, 2)
        items.append({
            "qid": f"T13-{i}", "dim": "DIM1", "type": "derivation-check",
            "prompt": f"Role A claims the aggregate success rate is {claimed_rate}. "
                      f"Recompute from the raw rows and answer derivable=true or "
                      f"false plus your recomputed value, as JSON "
                      f"{{\"derivable\":bool,\"recomputed\":x.xx}}.",
            "inputs": {"rows": rows, "claimed": claimed_rate},
            "expected": {"derivable": claimed_rate == true_rate,
                         "recomputed": true_rate},
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "evidence-schema-v1",
            "public": None})
    return items


# ── DIM2 写入门质量(8)──────────────────────────────────────────

def dim2():
    items = []
    # T2.1 毒写拒收 ×3(种子=10verdict 案:ev=true 无外部痕迹)
    for i in range(3):
        rows = []
        # 2 clean rows + 2 poisoned, order shuffled by rng
        rows.append({"row_id": "R1", "claim": "Agent A deployed version 2.1 on D2",
                     "evidence": {"url": "https://git.example/r1", "commit": "aa11"},
                     "fact_status": "verified", "external_verified": True})
        rows.append({"row_id": "R2", "claim": "Agent B plans migration on D5",
                     "evidence": {"mail_id": "M042"},
                     "fact_status": "planned", "external_verified": False})
        rows.append({"row_id": "R3", "claim": "Agent C fixed the payment bug",
                     "evidence": {}, "fact_status": "verified",
                     "external_verified": True})  # poisoned: ev=true, no evidence
        rows.append({"row_id": "R4", "claim": "Agent D achieved 99% accuracy",
                     "evidence": {"source": "self-report"},
                     "fact_status": "verified", "external_verified": False})  # 无据断言
        rng.shuffle(rows)
        gate_spec = ("Gate rule: admit a row only if (fact_status=verified implies "
                     "external evidence exists that is NOT self-produced) AND "
                     "(external_verified=true implies evidence is non-empty). "
                     "Answer with the JSON list of ADMITTED row_ids.")
        items.append({
            "qid": f"T21-{i}", "dim": "DIM2", "type": "gate-admit",
            "prompt": gate_spec,
            "inputs": {"rows": rows},
            "expected": ["R1", "R2"],
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "external-verified-provenance-v1",
            "public": None})
    # T2.2 去重题 ×3(近似重复阈值判定)
    for i in range(3):
        base = "Service X restarted after config push on D3"
        rows = [
            {"row_id": "R1", "text": base},
            {"row_id": "R2", "text": "Service X restarted after the config push on D3"},   # dup
            {"row_id": "R3", "text": "Service Y restarted after config push on D3"},        # not dup
            {"row_id": "R4", "text": "Service X halted before config push on D3"},          # not dup
        ]
        thr = 0.85
        # ground truth: Jaccard over word sets >= thr
        def jac(a, b):
            sa, sb = set(a.split()), set(b.split())
            return len(sa & sb) / len(sa | sb)
        dups = []
        for x in range(4):
            for y in range(x + 1, 4):
                if jac(rows[x]["text"], rows[y]["text"]) >= thr:
                    dups.append([rows[x]["row_id"], rows[y]["row_id"]])
        items.append({
            "qid": f"T22-{i}", "dim": "DIM2", "type": "dedup-threshold",
            "prompt": f"Rows enter a dedup gate: two rows are duplicates iff their "
                      f"word-set Jaccard similarity >= {thr}. Answer with the JSON list "
                      f"of duplicate PAIRS [row_x, row_y] (x before y), else [].",
            "inputs": {"rows": rows, "threshold": thr},
            "expected": dups,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "memory-dedup-v1",
            "public": None})
    # T2.3 语义门题 ×2(新事实与既有锚矛盾:拒/疑/收;种子=锚池偏差)
    anchors_variants = [
        ({"fact": "Deploy window is 10:00-12:00", "support": 40},
         [{"fact": "Deploy window is 10:00-12:00", "support": 40},
          {"fact": "Deploy window is 14:00-16:00", "support": 2}],
         "REJECT"),
        ({"fact": "Deploy window is 10:00-12:00", "support": 40},
         [{"fact": "Deploy window is 10:00-12:00", "support": 40},
          {"fact": "Deploy window is 10:30-12:30", "support": 12}],
         "QUARANTINE"),
    ]
    for i, (new_fact, pool, expected) in enumerate(anchors_variants):
        items.append({
            "qid": f"T23-{i}", "dim": "DIM2", "type": "semantic-gate",
            "prompt": "An anchor pool holds facts with support counts. A new fact "
                      "contradicts the top-supported fact if incompatible with it and "
                      "the pool's top fact has support >= 10x any competing variant. "
                      "Rule: REJECT the new fact if a contradicted top anchor's support "
                      ">= 10x the variant's; QUARANTINE if the variant's support is "
                      "within 10x; ADMIT otherwise. Answer REJECT|QUARANTINE|ADMIT.",
            "inputs": {"anchor_pool": pool, "new_fact": new_fact},
            "expected": expected,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer"}},
            "criteria_ref": "anchor-pool-selection-bias-v1",
            "public": None})
    return items


def main():
    items = dim1() + dim2()  # DIM3-4 follow; total must reach 30
    ds = {"seed": SEED, "split_seed": SPLIT_SEED, "n": len(items),
          "dims_done": ["DIM1", "DIM2"]}
    src = json.dumps({"meta": ds, "items": items}, ensure_ascii=False, sort_keys=True)
    (OUT / "decision_set.json").write_text(src, encoding="utf-8", newline="\n")
    import hashlib
    print(f"generated: {len(items)} items, sha256={hashlib.sha256(src.encode()).hexdigest()[:16]}")
    from collections import Counter
    print("by dim/type:", dict(Counter((it["dim"], it["type"]) for it in items)))


if __name__ == "__main__":
    main()
