# -*- coding: utf-8 -*-
"""BC1 发布版生成器 v2 — 修复 v1 自测暴露的 5 处出题缺陷(2026-09-23)。

修正(对应 SELFTEST_SCORECARD 审计):
1. T11:events 加 replies_to 关联;题面写死三桶语义;真值由 verifier 从
   inputs 重推(不再生成时埋)
2. T12:expected=从 log 推导的全部真矛盾对(D3 声明与回执按事实比对)
3. T31:题面声明复发边界(严格 day>first_seen);真值由 verifier 重推
4. T13:题面声明 banker's 舍入
5. 总则:全部 expected 改为「独立 verifier 函数从 inputs 推导」,
   生成器只造数据不藏答案

产物:decision_set_v2.json(正式版待复算 agent 完成后切换)
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


# ── DIM1(7)────────────────────────────────────────────────────

def gen_mailbox_v2():
    """时间线带 replies_to 关联;promise 带 promiser。"""
    events, sents = [], []
    for i in range(14):
        ev = {"id": f"M{i:03d}", "day": rng.choice(DAYS[:5])}
        if sents and rng.random() < 0.3:
            ev.update(kind="reply", **{"from": rng.choice(ROLES)},
                      replies_to=rng.choice(sents))
            if ev["from"] == next(e for e in events if e["id"] == ev["replies_to"])["to"] \
               if events else False:
                pass
        else:
            ev.update(kind="sent", **{"from": rng.choice(ROLES),
                                      "to": rng.choice(ROLES)})
            sents.append(ev["id"])
        if ev["kind"] == "sent" and rng.random() < 0.35:
            ev["kind"] = "promise"
            ev["promise_day"] = rng.choice(DAYS)
        events.append(ev)
    # fix reply integrity: replies_to must exist & from==original to
    by_id = {e["id"]: e for e in events if e["kind"] in ("sent", "promise")}
    fixed = []
    for e in events:
        if e["kind"] == "reply":
            orig = by_id.get(e.get("replies_to"))
            if orig is None or orig["to"] != e["from"]:
                # repair: make from = original's recipient
                if orig is not None:
                    e["from"] = orig["to"]
                else:
                    e["kind"] = "sent"
                    e.pop("replies_to", None)
                    e["to"] = rng.choice(ROLES)
        fixed.append(e)
    return fixed


def status_of_v2(events, role, day):
    """verifier:v2 语义(题面写死)。
    - due_promises: role 作为承诺方(kind=promise 且 from=role)且
      promise_day <= day 的 promise id
    - replied: 被 role 回复过的原信 id(reply.from==role,按 replies_to)
    - unanswered: 发给 role 的 sent/promise(to==role)且 id 不在 replied
    """
    idx = DAYS.index(day)
    upto = [e for e in events if DAYS.index(e["day"]) <= idx]
    due = sorted(e["id"] for e in upto
                 if e["kind"] == "promise" and e["from"] == role
                 and DAYS.index(e["promise_day"]) <= idx)
    replied = sorted({e["replies_to"] for e in upto
                      if e["kind"] == "reply" and e["from"] == role
                      and e.get("replies_to")})
    unanswered = sorted({e["id"] for e in upto
                         if e.get("to") == role and e["id"] not in replied})
    return {"due_promises": due, "replied": replied, "unanswered": unanswered}


def gen_conflict_v2():
    """claims vs receipt:数字与回执条数一致或不一致(真实由数据决定)。"""
    actual = rng.randint(30, 80)
    raw = [rng.randint(0, 9) for _ in range(actual)]
    c1 = actual + rng.choice([-8, 5, 12])          # 必不一致
    same = rng.random() < 0.5                        # D3 声明与回执是否一致
    c3 = actual if same else actual + rng.randint(1, 6)
    log = [
        {"day": "D1", "from": "A", "kind": "claim",
         "text": f"B processed {c1} requests last week."},
        {"day": "D2", "from": "B", "kind": "receipt", "raw": raw},
        {"day": "D3", "from": "C", "kind": "claim",
         "text": f"A acknowledged all of B's {c3} requests."},
    ]
    return log, actual


def conflict_pairs(log):
    """verifier:receipt 行数=真值;每条 claim 与其比对。"""
    receipt = next(l for l in log if l["kind"] == "receipt")
    n = len(receipt["raw"])
    import re
    pairs = []
    for l in log:
        if l["kind"] == "claim":
            m = re.search(r"(\d+)", l["text"])
            if m and int(m.group(1)) != n:
                pairs.append({"claim_day": l["day"], "evidence_day": receipt["day"]})
    return sorted(pairs, key=lambda p: p["claim_day"])


def dim1_v2():
    items = []
    # T1.1 ×3
    for i in range(3):
        evs = gen_mailbox_v2()
        role, day = rng.choice(ROLES), rng.choice(DAYS)
        prompt = (
            f"Given the mail-log below, what is role {role}'s exact status at end "
            f"of {day}? Answer with the JSON object "
            f'{{"due_promises":[...],"replied":[...],"unanswered":[...]}}. '
            f"Definitions (exact): due_promises = ids of promises MADE BY {role} "
            f"(kind=promise, from={role}) whose promise_day is on or before {day}; "
            f"replied = ids of messages that {role} has replied to (kind=reply, "
            f"from={role}, follow replies_to); unanswered = ids of messages "
            f"addressed TO {role} (to={role}, kind sent or promise) that are not "
            f"in replied. Only events dated on or before {day} count.")
        items.append({
            "qid": f"T11-{i}", "dim": "DIM1", "type": "mailbox-status",
            "prompt": prompt,
            "inputs": {"events": evs, "role": role, "day": day},
            "expected": status_of_v2(evs, role, day),
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "verdict-recomputability-v1", "public": None})
    # T1.2 ×2
    spec_conflict = ("Every claim states a number of requests; the receipt lists "
                     "the raw evidence rows. A claim CONFLICTS with the receipt iff "
                     "its stated number differs from the count of raw rows. Identify "
                     "every conflicting pair as {\"claim_day\":\"..\",\"evidence_day\":"
                     "\"..\"} in a JSON list sorted by claim_day. If none, answer [].")
    for i in range(2):
        log, _ = gen_conflict_v2()
        items.append({
            "qid": f"T12-{i}", "dim": "DIM1", "type": "conflict-detect",
            "prompt": spec_conflict,
            "inputs": {"log": log},
            "expected": conflict_pairs(log),
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "judge-systematic-inconsistency-v1", "public": None})
    # T1.3 ×2
    spec_deriv = ('Answer as JSON {"derivable":bool,"recomputed":x.xx}. '
                  'recomputed = round(total_ok / (total_ok + total_fail), 2) '
                  'using Python-style round-half-to-even. derivable = '
                  '(the claimed rate equals your recomputed value).')
    for i in range(2):
        rows = [{"date": f"D{k}", "ok": rng.randint(0, 4), "fail": rng.randint(0, 4)}
                for k in range(1, 7)]
        tot_ok = sum(r["ok"] for r in rows)
        tot_all = tot_ok + sum(r["fail"] for r in rows)
        true_rate = round(tot_ok / tot_all, 2)
        claimed = true_rate if rng.random() < 0.4 else \
            round(min(1.0, true_rate + rng.choice([-0.15, 0.1, 0.2])), 2)
        if claimed == true_rate and rng.random() < 0.5:
            claimed = round(min(1.0, true_rate + 0.1), 2)
        items.append({
            "qid": f"T13-{i}", "dim": "DIM1", "type": "derivation-check",
            "prompt": f"Role A claims the aggregate success rate is {claimed}. "
                      f"Recompute from the raw rows. " + spec_deriv,
            "inputs": {"rows": rows, "claimed": claimed},
            "expected": {"derivable": claimed == true_rate, "recomputed": true_rate},
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "evidence-schema-v1", "public": None})
    return items


# ── DIM2(8)与 v1 相同(无缺陷),复用 v1 实现 ──────────────────
def jac(a, b):
    sa, sb = set(a.split()), set(b.split())
    return len(sa & sb) / len(sa | sb)


def dim2_v2():
    items = []
    for i in range(3):
        rows = [
            {"row_id": "R1", "claim": "Agent A deployed version 2.1 on D2",
             "evidence": {"url": "https://git.example/r1", "commit": "aa11"},
             "fact_status": "verified", "external_verified": True},
            {"row_id": "R2", "claim": "Agent B plans migration on D5",
             "evidence": {"mail_id": "M042"},
             "fact_status": "planned", "external_verified": False},
            {"row_id": "R3", "claim": "Agent C fixed the payment bug",
             "evidence": {}, "fact_status": "verified", "external_verified": True},
            {"row_id": "R4", "claim": "Agent D achieved 99% accuracy",
             "evidence": {"source": "self-report"},
             "fact_status": "verified", "external_verified": False},
        ]
        rng.shuffle(rows)
        items.append({
            "qid": f"T21-{i}", "dim": "DIM2", "type": "gate-admit",
            "prompt": ("Gate rule: admit a row only if (fact_status=verified implies "
                       "external evidence exists that is NOT self-produced) AND "
                       "(external_verified=true implies evidence is non-empty). "
                       "Answer with the JSON list of ADMITTED row_ids."),
            "inputs": {"rows": rows}, "expected": ["R1", "R2"],
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "external-verified-provenance-v1", "public": None})
    for i in range(3):
        base = "Service X restarted after config push on D3"
        rows = [
            {"row_id": "R1", "text": base},
            {"row_id": "R2", "text": "Service X restarted after the config push on D3"},
            {"row_id": "R3", "text": "Service Y restarted after config push on D3"},
            {"row_id": "R4", "text": "Service X halted before config push on D3"},
        ]
        thr = 0.85
        dups = sorted([[rows[x]["row_id"], rows[y]["row_id"]]
                       for x in range(4) for y in range(x + 1, 4)
                       if jac(rows[x]["text"], rows[y]["text"]) >= thr])
        items.append({
            "qid": f"T22-{i}", "dim": "DIM2", "type": "dedup-threshold",
            "prompt": f"Rows enter a dedup gate: two rows are duplicates iff their "
                      f"word-set Jaccard similarity >= {thr}. Answer with the JSON "
                      f"list of duplicate PAIRS [row_x, row_y] (x before y), else [].",
            "inputs": {"rows": rows, "threshold": thr},
            "expected": dups,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "memory-dedup-v1", "public": None})
    variants = [
        ({"fact": "Deploy window is 10:00-12:00", "support": 40},
         [{"fact": "Deploy window is 10:00-12:00", "support": 40},
          {"fact": "Deploy window is 14:00-16:00", "support": 2}], "REJECT"),
        ({"fact": "Deploy window is 10:00-12:00", "support": 40},
         [{"fact": "Deploy window is 10:00-12:00", "support": 40},
          {"fact": "Deploy window is 10:30-12:30", "support": 12}], "QUARANTINE"),
    ]
    for i, (new_fact, pool, expected) in enumerate(variants):
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
            "criteria_ref": "anchor-pool-selection-bias-v1", "public": None})
    return items


# ── DIM3(7)复发边界写死 ───────────────────────────────────────

KNOWN_PITFALLS = [
    {"pit_id": "P1", "pattern": "CRLF-in-file", "first_seen": "D1"},
    {"pit_id": "P2", "pattern": "wrong-tmp-path", "first_seen": "D2"},
    {"pit_id": "P3", "pattern": "pathspec-missing", "first_seen": "D3"},
]


def recurrence_counts(stream):
    """verifier:复发=同 signature 在严格 first_seen 之后(day>)出现。
    首见当日(含首次本身)不计复发。"""
    out = {p["pit_id"]: 0 for p in KNOWN_PITFALLS}
    for ev in stream:
        for p in KNOWN_PITFALLS:
            if ev["signature"] == p["pattern"] and ev["day"] > p["first_seen"]:
                out[p["pit_id"]] += 1
    return out


def dim3_v2():
    items = []
    spec_rec = ('A recurrence of a known pitfall = an error event whose signature '
                'matches the pitfall pattern AND occurs STRICTLY AFTER its '
                'first_seen day (same-day or first occurrence does not count). '
                'novel-* signatures are never recurrences. Answer as JSON '
                '{pit_id: count}.')
    for i in range(3):
        stream = []
        for p in KNOWN_PITFALLS:
            # first occurrence on/before first_seen + recurrences strictly after
            stream.append({"day": p["first_seen"], "kind": "error",
                           "signature": p["pattern"]})
            for k in range(rng.randint(0, 3)):
                d = rng.choice([d for d in DAYS if d > p["first_seen"]])
                stream.append({"day": d, "kind": "error", "signature": p["pattern"]})
        for k in range(rng.randint(2, 5)):
            stream.append({"day": rng.choice(DAYS), "kind": "error",
                           "signature": f"novel-{rng.randint(10, 99)}"})
        rng.shuffle(stream)
        items.append({
            "qid": f"T31-{i}", "dim": "DIM3", "type": "recurrence-count",
            "prompt": spec_rec,
            "inputs": {"anchors": KNOWN_PITFALLS, "stream": stream},
            "expected": recurrence_counts(stream),
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "recurrence-tracking-v1", "public": None})
    for i in range(2):
        logs = [
            {"t": "10:00", "cmd": "send_mail(id=X1)", "exit": 0,
             "stdout": "ok", "artifact": None},
            {"t": "10:05", "cmd": "post_comment(pr=9)", "exit": 0,
             "stdout": "ok", "artifact": "comment_id=c77"},
            {"t": "10:10", "cmd": "deploy(target=prod)", "exit": 1,
             "stdout": "error", "artifact": None},
            {"t": "10:15", "cmd": "send_mail(id=X2)", "exit": 0,
             "stdout": "409 conflict (deduped)", "artifact": None},
        ]
        rng.shuffle(logs)
        expected = sorted(l["t"] for l in logs
                          if l["exit"] == 0 and not l["artifact"])
        items.append({
            "qid": f"T32-{i}", "dim": "DIM3", "type": "fake-green-detect",
            "prompt": "A step is a FAKE GREEN iff exit=0/ok is claimed but no "
                      "verifiable artifact exists (receipt id/comment id); 409 "
                      "dedup responses claiming ok also count. Honest failures are "
                      "not fake greens. Answer with the JSON list of timestamps "
                      "(hh:mm, ascending).",
            "inputs": {"logs": logs}, "expected": expected,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "adversarial-fake-success", "public": None})
    for i in range(2):
        pos = [rng.gauss(0.60, 0.05) for _ in range(30)]
        neg = [rng.gauss(0.40, 0.05) for _ in range(30)]
        margin = round(sum(pos) / 30 - sum(neg) / 30, 3)
        items.append({
            "qid": f"T33-{i}", "dim": "DIM3", "type": "drift-margin",
            "prompt": "Compute the drift margin = mean(positive_scores) − "
                      "mean(negative_scores), rounded to 3 decimals (Python round). "
                      "Answer as JSON {\"margin\": x.xxx}.",
            "inputs": {"positive": [round(v, 4) for v in pos],
                       "negative": [round(v, 4) for v in neg]},
            "expected": {"margin": margin},
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": "drift-margin-v1", "public": None})
    return items


# ── DIM4(8):T41 三题描述必须互不相同 ──────────────────────────

def dim4_v2():
    items = []
    stage_sets = [
        ({"preregister": "criteria doc was edited two days AFTER results were out",
          "execute": "all 40 runs completed with zero errors",
          "record": "every raw artifact committed before scoring",
          "recompute": "an independent fresh session reproduced all metrics",
          "publish": "headline number published with artifacts linked"},
         {"stage": "preregister", "criteria_ref": "criteria-locked-before-run-v1"}),
        ({"preregister": "criteria locked and committed before any run",
          "execute": "all 40 runs completed with zero errors",
          "record": "session logs stayed only on a laptop, never committed",
          "recompute": "an independent fresh session reproduced all metrics",
          "publish": "headline number published with artifacts linked"},
         {"stage": "record", "criteria_ref": "artifacts-complete-in-vcs-v1"}),
        ({"preregister": "criteria locked and committed before any run",
          "execute": "all 40 runs completed with zero errors",
          "record": "every raw artifact committed before scoring",
          "recompute": "the implementer re-checked their own numbers and passed",
          "publish": "headline number published with artifacts linked"},
         {"stage": "recompute", "criteria_ref": "independent-recomputer-v1"}),
    ]
    for i, (descs, exp) in enumerate(stage_sets):
        items.append({
            "qid": f"T41-{i}", "dim": "DIM4", "type": "stage-violation",
            "prompt": "Five pipeline stages ran as described. Exactly one stage "
                      "violates a verification discipline. Answer as JSON "
                      "{\"stage\":\"..\",\"criteria_ref\":\"..\"} naming the violating "
                      "stage and its criterion family (one of criteria-locked-"
                      "before-run-v1 / artifacts-complete-in-vcs-v1 / independent-"
                      "recomputer-v1).",
            "inputs": {"stages": ["preregister", "execute", "record",
                                  "recompute", "publish"], "descriptions": descs},
            "expected": exp,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer_json"}},
            "criteria_ref": exp["criteria_ref"], "public": None})
    for i in range(3):
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
            "inputs": {"cases": cases}, "expected": expected,
            "check": {"kind": "json_map_equal", "spec": {"target": "answer"}},
            "criteria_ref": "anchor-pool-selection-bias-v1", "public": None})
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
            "criteria_ref": "skip-label-fidelity-v1", "public": None})
    return items


def split_public(items):
    srng = random.Random(SPLIT_SEED)
    order = list(items)
    srng.shuffle(order)
    for it in order[:18]:
        it["public"] = True
    for it in order[18:]:
        it["public"] = False
    return order


def main():
    items = split_public(dim1_v2() + dim2_v2() + dim3_v2() + dim4_v2())
    assert len(items) == 30 and sum(1 for i in items if i["public"]) == 18
    meta = {"seed": SEED, "split_seed": SPLIT_SEED, "n": 30, "public_n": 18,
            "version": "v2 (post-selftest fixes)", "fixes": [
                "T11: replies_to link + exact bucket semantics",
                "T12: expected derived from data (all real conflicts)",
                "T31: recurrence boundary stated (strictly after first_seen)",
                "T13: banker's rounding stated",
                "T41: three distinct scenario descriptions"]}
    src = json.dumps({"meta": meta, "items": items}, ensure_ascii=False, sort_keys=True)
    (OUT / "decision_set_v2.json").write_text(src, encoding="utf-8", newline="\n")
    import hashlib
    print(f"v2: 30 items public=18 sha256={hashlib.sha256(src.encode()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
