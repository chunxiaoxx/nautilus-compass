# -*- coding: utf-8 -*-
"""Independent recompute for three jev-trust domain-calibration artifacts.

Non-implementer recomputation, 2026-09-22. Reads ONLY:
  PROTOCOL.md / decision_set.json / session.jsonl / session.jsonl.sig / pubkey.txt
Does NOT read stats.json or RESULTS.md (that happens in a later, separate step).
Writes independent results to runtime/_indep_results_20260922.json
"""
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
DOMAINS = [
    ("domain1_python-exception-prediction", "jev_trust_dogfood_20260922"),
    ("domain2_code-patch-behavior", "jev_trust_domain2_20260922"),
    ("domain3_embodied-qc-labeling", "jev_trust_domain3_20260922"),
]


# ---------------------------------------------------------------- truth re-derivation

def truth_domain1(item):
    """Exec the code, run the call, truth=1 iff an exception is raised."""
    ns = {}
    exec(item["state"]["code"], ns)  # defines f
    try:
        eval(item["state"]["call"], ns)
        return 0
    except Exception:
        return 1


def _run_pair(code, args):
    ns = {}
    exec(code, ns)
    f = ns["f"]
    try:
        ret = f(*args)
        return ("ok", str(ret))
    except Exception as e:
        return ("exc", type(e).__name__)


def truth_domain2(item):
    """Exec both versions, compare (status, value/exception-type-name)."""
    args = json.loads(item["state"]["call_args"])
    before = _run_pair(item["state"]["code_before"], args)
    after = _run_pair(item["state"]["code_after"], args)
    return (1 if before != after else 0), before, after


def truth_domain3(item, strict_mono=False):
    """Four-rule verifier per PROTOCOL.md, implemented from the protocol text.

    strict_mono=False: monotonic means non-strict (diffs all >=0 or all <=0).
    """
    r = item["state"]["joint_readings"]
    # rule 1: adjacent |diff| > 0.8  (spike)
    spike = any(abs(r[i + 1] - r[i]) > 0.8 for i in range(len(r) - 1))
    # rule 2: run of >=5 consecutive identical readings (stuck)
    stuck = False
    run = 1
    for i in range(1, len(r)):
        if r[i] == r[i - 1]:
            run += 1
            if run >= 5:
                stuck = True
                break
        else:
            run = 1
    # rule 3: any reading outside [-3.14, 3.14] (limit)
    limit = any(x > 3.14 or x < -3.14 for x in r)
    # rule 4: |first-last| > 1.5 AND whole sequence monotone inc or dec (drift)
    drift_amp = abs(r[0] - r[-1]) > 1.5
    diffs = [r[i + 1] - r[i] for i in range(len(r) - 1)]
    if strict_mono:
        mono = all(d > 0 for d in diffs) or all(d < 0 for d in diffs)
    else:
        mono = all(d >= 0 for d in diffs) or all(d <= 0 for d in diffs)
    drift = drift_amp and mono
    return 1 if (spike or stuck or limit or drift) else 0


# ---------------------------------------------------------------- metrics (hand implementation)

def bin_of(conf, nbins=10):
    return min(int(conf * nbins), nbins - 1)


def hand_metrics(preds):
    """preds: list of (qid, truth01, decision_yes_no, stated_conf).

    Hand-computed accuracy / brier / ece / C per PROTOCOL.md formulas.
    """
    n = len(preds)
    recs = []
    for qid, truth, decision, conf in preds:
        p_yes = conf if decision == "yes" else 1.0 - conf
        p_true = p_yes if truth == 1 else 1.0 - p_yes
        correct = 1 if ((decision == "yes") == (truth == 1)) else 0
        top_conf = max(p_yes, 1.0 - p_yes)
        recs.append(dict(qid=qid, truth=truth, decision=decision, conf=conf,
                         p_yes=p_yes, p_true=p_true, correct=correct,
                         top_conf=top_conf))
    acc = sum(r["correct"] for r in recs) / n
    brier = sum((1.0 - r["p_true"]) ** 2 for r in recs) / n
    bins = defaultdict(lambda: [0, 0.0, 0])  # cnt, conf_sum, correct_sum
    for r in recs:
        b = bin_of(r["top_conf"])
        bins[b][0] += 1
        bins[b][1] += r["top_conf"]
        bins[b][2] += r["correct"]
    ece = 0.0
    bin_table = {}
    for b, (cnt, csum, cor) in sorted(bins.items()):
        bar = (cnt / n) * abs(cor / cnt - csum / cnt)
        bin_table[b] = dict(n=cnt, acc=cor / cnt, conf=csum / cnt, contrib=bar)
        ece += bar
    return dict(n=n, correct=sum(r["correct"] for r in recs), accuracy=acc,
                brier=brier, ece=ece, C=1.0 - ece, bin_table=bin_table,
                recs=recs)


# ---------------------------------------------------------------- per-domain pipeline

def process(name, folder):
    d = os.path.join(BASE, folder)
    out = {"domain": name, "folder": folder}

    # step 1: signature verification (three-state from ReceiptResult)
    import jev_trust
    pub_hex = open(os.path.join(d, "pubkey.txt"), encoding="utf-8").read().strip()
    rr = jev_trust.verify_log(os.path.join(d, "session.jsonl"),
                              os.path.join(d, "session.jsonl.sig"), pub_hex)
    out["verify"] = {"valid": bool(getattr(rr, "valid", None)),
                     "repr": repr(rr)}

    # step 2: sha256 of decision_set.json (computed BEFORE opening stats.json)
    raw = open(os.path.join(d, "decision_set.json"), "rb").read()
    out["decision_set_sha256"] = hashlib.sha256(raw).hexdigest()
    ds = json.loads(raw)
    out["decision_set_n"] = len(ds)

    # step 3: independent truth re-derivation
    my_truth = {}
    mismatches = []
    extra = {}
    if name.startswith("domain1"):
        for it in ds:
            t = truth_domain1(it)
            my_truth[it["qid"]] = t
            if t != it["truth"]:
                mismatches.append((it["qid"], "ds", it["truth"], t))
    elif name.startswith("domain2"):
        res_pairs = {}
        for it in ds:
            t, before, after = truth_domain2(it)
            my_truth[it["qid"]] = t
            if t != it["truth"]:
                mismatches.append((it["qid"], "ds", it["truth"], t))
            # extra evidence: stored before/after vs my exec results
            if list(before) != it.get("before_result") or list(after) != it.get("after_result"):
                res_pairs[it["qid"]] = dict(stored_b=it.get("before_result"),
                                            mine_b=list(before),
                                            stored_a=it.get("after_result"),
                                            mine_a=list(after))
        extra["stored_result_repr_diffs"] = res_pairs
    else:
        t_strict_diff = []
        for it in ds:
            t = truth_domain3(it)
            t2 = truth_domain3(it, strict_mono=True)
            if t != t2:
                t_strict_diff.append(it["qid"])
            my_truth[it["qid"]] = t
            if t != it["truth"]:
                mismatches.append((it["qid"], "ds", it["truth"], t))
        extra["mono_variant_diffs"] = t_strict_diff
        # pattern distribution + positive share
        extra["pattern_counts"] = dict(Counter(it["pattern"] for it in ds))
        extra["truth_counts"] = dict(Counter(it["truth"] for it in ds))
    out["truth_mismatch_count"] = len(mismatches)
    out["truth_mismatches"] = mismatches
    out["extra"] = extra

    # step 5 (a): session.jsonl structure / completeness
    lines = [json.loads(l) for l in open(os.path.join(d, "session.jsonl"), encoding="utf-8") if l.strip()]
    kinds = Counter(l.get("kind") for l in lines)
    out["session_line_counts"] = dict(kinds)
    out["session_total_lines"] = len(lines)
    errs = [l for l in lines if l.get("kind") == "error" or "error" in str(l.get("kind", "")).lower()
            or l.get("status") == "error" or l.get("error")]
    out["error_lines"] = errs

    calls = [l for l in lines if l.get("kind") == "call"]
    outs = [l for l in lines if l.get("kind") == "outcome"]
    out["n_calls"] = len(calls)
    out["n_outcomes"] = len(outs)
    out["call_qids_unique"] = len(set(c["qid"] for c in calls)) == len(calls)
    out["outcome_qids_unique"] = len(set(c["qid"] for c in outs)) == len(outs)
    out["call_outcome_qid_sets_equal"] = (set(c["qid"] for c in calls)
                                          == set(o["qid"] for o in outs))

    # outcome-line truth vs decision_set truth vs my truth
    ds_truth = {it["qid"]: it["truth"] for it in ds}
    out_truth_mismatch_vs_ds = [o["qid"] for o in outs if o["truth"] != ds_truth.get(o["qid"])]
    out_truth_mismatch_vs_mine = [o["qid"] for o in outs if o["truth"] != my_truth.get(o["qid"])]
    out["outcome_truth_vs_decision_set_mismatches"] = out_truth_mismatch_vs_ds
    out["outcome_truth_vs_mytruth_mismatches"] = out_truth_mismatch_vs_mine

    # step 4: metrics from call lines ONLY (+ my independently re-derived truth)
    preds = []
    call_meta_issues = []
    for c in calls:
        qid = c["qid"]
        if qid not in my_truth:
            call_meta_issues.append(("no_truth", qid))
            continue
        dec = c.get("decision")
        conf = c.get("stated_confidence")
        if dec not in ("yes", "no"):
            call_meta_issues.append(("bad_decision", qid, dec))
            continue
        if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
            call_meta_issues.append(("bad_conf", qid, conf))
            continue
        preds.append((qid, my_truth[qid], dec, float(conf)))
    out["call_meta_issues"] = call_meta_issues
    m = hand_metrics(preds)
    out["metrics"] = {k: v for k, v in m.items() if k != "recs"}
    out["_recs"] = m["recs"]

    # cross-checks against outcome-line fields (correct / p_true as logged)
    rec_by_qid = {r["qid"]: r for r in m["recs"]}
    oc_diff = []
    for o in outs:
        r = rec_by_qid.get(o["qid"])
        if r is None:
            continue
        if o.get("correct") != r["correct"] or abs(float(o.get("p_true")) - r["p_true"]) > 1e-9:
            oc_diff.append((o["qid"], o.get("correct"), r["correct"],
                            o.get("p_true"), round(r["p_true"], 8)))
    out["outcome_logged_vs_my_calc_diffs"] = oc_diff

    # library cross-check (protocol: hand calc and jev_trust.calib must agree)
    from jev_trust.calib import Prediction, CalibrationState
    st = CalibrationState()
    for r in m["recs"]:
        st.add(Prediction(qid=r["qid"], stated_confidence=r["top_conf"],
                          correct=r["correct"], p_true=r["p_true"]))
    out["lib_crosscheck"] = dict(accuracy=st.accuracy, brier=jev_trust.brier(st.preds)
                                 if hasattr(jev_trust, "brier") else None,
                                 ece=jev_trust.ece_toplabel(st.preds))
    return out


def main():
    results = {}
    for name, folder in DOMAINS:
        print(f"\n{'='*70}\n{name}  ({folder})\n{'='*70}")
        r = process(name, folder)
        results[name] = r
        print("verify        :", r["verify"])
        print("ds sha256     :", r["decision_set_sha256"])
        print("ds n          :", r["decision_set_n"])
        print("truth mismatch:", r["truth_mismatch_count"], r["truth_mismatches"][:10])
        if "pattern_counts" in r["extra"]:
            print("patterns      :", r["extra"]["pattern_counts"])
            print("truth counts  :", r["extra"]["truth_counts"])
            print("mono variant qid diffs (nonstrict vs strict):", r["extra"]["mono_variant_diffs"])
        if "stored_result_repr_diffs" in r["extra"]:
            print("stored before/after vs my exec repr diffs:", len(r["extra"]["stored_result_repr_diffs"]))
            for qid, v in list(r["extra"]["stored_result_repr_diffs"].items())[:5]:
                print("   ", qid, v)
        print("lines         :", r["session_line_counts"], "total", r["session_total_lines"])
        print("error lines   :", len(r["error_lines"]))
        print("call/outcome  :", r["n_calls"], r["n_outcomes"],
              "unique_ok", r["call_qids_unique"], r["outcome_qids_unique"],
              "sets_equal", r["call_outcome_qid_sets_equal"])
        print("outcome.truth vs ds truth mismatches :", r["outcome_truth_vs_decision_set_mismatches"])
        print("outcome.truth vs MY truth mismatches :", r["outcome_truth_vs_mytruth_mismatches"])
        print("outcome logged correct/p_true diffs  :", len(r["outcome_logged_vs_my_calc_diffs"]),
              r["outcome_logged_vs_my_calc_diffs"][:5])
        mm = r["metrics"]
        print("MY metrics    : n=%d correct=%d acc=%.6f brier=%.8f ece=%.8f C=%.8f"
              % (mm["n"], mm["correct"], mm["accuracy"], mm["brier"], mm["ece"], mm["C"]))
        print("bin table     :")
        for b, t in mm["bin_table"].items():
            print("   bin%d n=%d acc=%.4f conf=%.4f contrib=%.6f"
                  % (b, t["n"], t["acc"], t["conf"], t["contrib"]))
        print("lib crosscheck:", r["lib_crosscheck"])

    slim = {}
    for k, v in results.items():
        slim[k] = {kk: vv for kk, vv in v.items() if kk not in ("_recs", "extra")}
        slim[k]["pattern_counts"] = results[k]["extra"].get("pattern_counts")
        slim[k]["truth_counts"] = results[k]["extra"].get("truth_counts")
    with open(os.path.join(BASE, "_indep_results_20260922.json"), "w", encoding="utf-8") as f:
        json.dump(slim, f, ensure_ascii=False, indent=1)
    print("\nindependent results written to runtime/_indep_results_20260922.json")
    print("stats.json NOT touched in this step.")


if __name__ == "__main__":
    main()
