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


# ── DIM3 重犯率(7)──────────────────────────────────────────────

KNOWN_PITFALLS = [
    {"pit_id": "P1", "pattern": "CRLF-in-file",  "first_seen": "D1"},
    {"pit_id": "P2", "pattern": "wrong-tmp-path", "first_seen": "D2"},
    {"pit_id": "P3", "pattern": "pathspec-missing", "first_seen": "D3"},
]


def dim3():
    items = []
    # T3.1 复发计数题 ×3(历史锚+新行为流,数复发)
    for i in range(3):
        behavior = []
        # seed stream: each known pitfall recurs 0-3 times + noise events
        counts = {p["pit_id"]: rng.randint(0, 3) for p in KNOWN_PITFALLS}
        for p in KNOWN_PITFALLS:
            for k in range(counts[p["pit_id"]]):
                behavior.append({"day": rng.choice(DAYS), "kind": "error",
                                 "signature": p["pattern"]})
        for k in range(rng.randint(2, 5)):
            behavior.append({"day": rng.choice(DAYS), "kind": "error",
                             "signature": f"novel-{rng.randint(10,99)}"})
        rng.shuffle(behavior)
        expected = {p["pit_id"]: counts[p["pit_id"]] for p in KNOWN_PITFALLS}
        items.append({
            "qid": f"T31-{i}", "dim": "DIM3", "type": "recurrence-count",
            "prompt": "Given the known-pitfall anchors and a behavior stream, count "
                      "how many times EACH known pitfall recurs (novel-* signatures "
                      "are not recurrences). Answer as JSON {pit_id: count}.",
            "inputs": {"anchors": KNOWN_PITFALLS, "stream": behavior},
            "expected": expected,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "recurrence-tracking-v1",
            "public": None})
    # T3.2 假绿识别题 ×2(种子=409 去重吞函/gh 评论静默失败:说 OK 但产物缺)
    for i in range(2):
        logs = [
            {"t": "10:00", "cmd": "send_mail(id=X1)", "exit": 0,
             "stdout": "ok", "artifact": None},          # fake green: no receipt id
            {"t": "10:05", "cmd": "post_comment(pr=9)", "exit": 0,
             "stdout": "ok", "artifact": "comment_id=c77"},  # real green
            {"t": "10:10", "cmd": "deploy(target=prod)", "exit": 1,
             "stdout": "error", "artifact": None},          # honest red
            {"t": "10:15", "cmd": "send_mail(id=X2)", "exit": 0,
             "stdout": "409 conflict (deduped)", "artifact": None},  # fake green: 409 吞
        ]
        rng.shuffle(logs)
        expected = sorted([l["t"] for l in logs
                           if l["exit"] == 0 and not l["artifact"]])
        items.append({
            "qid": f"T32-{i}", "dim": "DIM3", "type": "fake-green-detect",
            "prompt": "A step is a FAKE GREEN iff exit=0/ok is claimed but no "
                      "verifiable artifact exists (receipt id/comment id); 409 "
                      "dedup responses claiming ok also count. Honest failures are "
                      "not fake greens. Answer with the JSON list of timestamps "
                      "(hh:mm, ascending).",
            "inputs": {"logs": logs},
            "expected": expected,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "adversarial-fake-success",
            "public": None})
    # T3.3 漂移 margin 题 ×2(pos−neg 对照)
    for i in range(2):
        pos = [rng.gauss(0.60, 0.05) for _ in range(30)]
        neg = [rng.gauss(0.40, 0.05) for _ in range(30)]
        margin = round(sum(pos) / 30 - sum(neg) / 30, 3)
        items.append({
            "qid": f"T33-{i}", "dim": "DIM3", "type": "drift-margin",
            "prompt": "Compute the drift margin = mean(positive_scores) − "
                      "mean(negative_scores), rounded to 3 decimals. Answer as "
                      "JSON {\"margin\": x.xxx}.",
            "inputs": {"positive": [round(v, 4) for v in pos],
                       "negative": [round(v, 4) for v in neg]},
            "expected": {"margin": margin},
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "drift-margin-v1",
            "public": None})
    return items


# ── DIM4 归因可追溯(8)──────────────────────────────────────────

PIPELINE_STAGES = ["preregister", "execute", "record", "recompute", "publish"]


def dim4():
    items = []
    # T4.1 环节违例题 ×3(五环节链,判哪个环节违哪条判据)
    violations = [
        ("preregister", "criteria-locked-before-run-v1"),
        ("record", "artifacts-complete-in-vcs-v1"),
        ("recompute", "independent-recomputer-v1"),
    ]
    stage_texts = {
        "preregister": "criteria doc was edited two days AFTER results were out",
        "execute": "all 40 runs completed with zero errors",
        "record": "session log files stayed only on a laptop (never committed)",
        "recompute": "the implementer re-checked their own numbers and passed",
        "publish": "headline number published with all raw artifacts linked",
    }
    for i, (stage, crit) in enumerate(violations):
        items.append({
            "qid": f"T41-{i}", "dim": "DIM4", "type": "stage-violation",
            "prompt": "Five pipeline stages ran as described. Exactly one stage "
                      "violates a verification discipline. Answer as JSON "
                      "{\"stage\":\"..\",\"criteria_ref\":\"..\"} naming the violating "
                      "stage and the criterion family (one of criteria-locked-"
                      "before-run-v1 / artifacts-complete-in-vcs-v1 / independent-"
                      "recomputer-v1).",
            "inputs": {"stages": PIPELINE_STAGES, "descriptions": stage_texts},
            "expected": {"stage": stage, "criteria_ref": crit},
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": crit,
            "public": None})
    # T4.2 锚池审判题 ×3(种子=sim50:池构成偏差一拦一放)
    for i in range(3):
        # symmetric firing -> the RULE itself is over-firing (RULE_GUILTY);
        # one-sided firing (only against-agent) -> selection bias in the POOL
        both = i < 2
        cases = [
            {"case": "F1", "pool_bias": "against-agent", "fired": True},
            {"case": "F2", "pool_bias": "for-agent", "fired": both},
            {"case": "F3", "pool_bias": "none", "fired": False},
        ]
        expected = "RULE_GUILTY" if both else "POOL_GUILTY"
        items.append({
            "qid": f"T42-{i}", "dim": "DIM4", "type": "anchor-pool-verdict",
            "prompt": "A guard rule examines flagged cases drawn from an anchor "
                      "pool. F1 (pool biased against the agent) fired. "
                      f"{'F2 (identical violation shape, pool biased FOR the agent) also fired.' if both else 'F2 (identical violation shape, pool biased FOR the agent) did NOT fire.'} "
                      "F3 (clean control) never fired. Judging from firing "
                      "symmetry alone: if the rule fires on BOTH biased sides, the "
                      "rule itself is over-firing — answer RULE_GUILTY; if it fires "
                      "only against one side while sparing the identical "
                      "for-agent case, the pool's composition is guilty of "
                      "selection bias — answer POOL_GUILTY.",
            "inputs": {"cases": cases},
            "expected": expected,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer"}},
            "criteria_ref": "anchor-pool-selection-bias-v1",
            "public": None})
    # T4.3 skip 标签保真 ×2(结局 vs 病因双问;种子=f08c/d821)
    for i in range(2):
        items.append({
            "qid": f"T43-{i}", "dim": "DIM4", "type": "skip-label-fidelity",
            "prompt": "A run was skipped. Decide the label: SKIP_OUTCOME (the "
                      "outcome did not happen — e.g. dependency never ran) vs "
                      "SKIP_CAUSE (the cause was avoided — e.g. the failure mode "
                      "was prevented upstream). Labels must not be swapped. "
                      "Answer SKIP_OUTCOME or SKIP_CAUSE.",
            "inputs": {"narrative": [
                "Upstream fix landed, so the failure mode never got a chance to "
                "trigger; the detector run had nothing to detect." if i == 0 else
                "The dependency job was cancelled by an operator, so this stage "
                "never executed at all."]},
            "expected": "SKIP_CAUSE" if i == 0 else "SKIP_OUTCOME",
            "check": {"kind": "json_map_equal", "spec": {"target": "answer"}},
            "criteria_ref": "skip-label-fidelity-v1",
            "public": None})
    return items


def split_public(items):
    """18/12 切分,SPLIT_SEED 独立(判据 4)。holdout qid 封存另档。"""
    srng = random.Random(SPLIT_SEED)
    order = list(items)
    srng.shuffle(order)
    for it in order[:18]:
        it["public"] = True
    for it in order[18:]:
        it["public"] = False
    return order


def main():
    items = split_public(dim1() + dim2() + dim3() + dim4())
    assert len(items) == 30, len(items)
    assert sum(1 for it in items if it["public"]) == 18
    ds = {"seed": SEED, "split_seed": SPLIT_SEED, "n": len(items),
          "dims_done": ["DIM1", "DIM2", "DIM3", "DIM4"], "public_n": 18}
    src = json.dumps({"meta": ds, "items": items}, ensure_ascii=False, sort_keys=True)
    (OUT / "decision_set.json").write_text(src, encoding="utf-8", newline="\n")
    import hashlib
    print(f"generated: {len(items)} items, public=18 holdout=12, "
          f"sha256={hashlib.sha256(src.encode()).hexdigest()}")
    from collections import Counter
    print("by dim:", dict(Counter(it['dim'] for it in items)))


if __name__ == "__main__":
    main()
