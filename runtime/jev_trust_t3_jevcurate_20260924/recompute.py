"""T3 mini recompute — non-implementer script.

Step 3: recompute all PROTOCOL.md metrics from blind_pack.json readings
using the recompute agent's OWN blind labels (blind_labels.json).
Step 4 support: also recompute implementer-label metrics from
t3_results.json raw_main to check implementer arithmetic reproducibility,
and cross-check reading transcription across artifacts.
No API calls. stdlib only.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def noul_metrics(rows):
    """rows: list of (p, y). conf for ECE = p (noul answers carry no conf)."""
    n = len(rows)
    acc = sum(1 for p, y in rows if (p >= 0.70) == (y == 1)) / n
    brier = sum((p - y) ** 2 for p, y in rows) / n
    # ECE, 10 equal-width bins on [0,1]; top edge 1.0 goes to last bin
    bins = [[] for _ in range(10)]
    for p, y in rows:
        k = min(int(p * 10), 9)
        bins[k].append((p, y))
    ece = 0.0
    detail = []
    for k, b in enumerate(bins):
        if not b:
            continue
        conf_k = sum(p for p, _ in b) / len(b)
        acc_k = sum(y for _, y in b) / len(b)
        w = len(b) / n
        ece += w * abs(acc_k - conf_k)
        detail.append({"bin": k, "n": len(b), "conf_k": round(conf_k, 6),
                       "acc_k": acc_k, "|acc-conf|": round(abs(acc_k - conf_k), 6)})
    return {"accuracy@0.70": round(acc, 6), "brier": round(brier, 6),
            "ece10": round(ece, 6), "bins": detail}


def depth_metrics(pairs, confs):
    """pairs: list of (s_1based, d). confs: list of depth answer confs."""
    n = len(pairs)
    mae = sum(abs(s - d) for s, d in pairs) / n
    acc = sum(1 for s, d in pairs if (s >= 3.0) == (d >= 3)) / n
    low = [rid for rid, c in confs.items() if c < 0.5]
    return {"mae": round(mae, 6), "accuracy@3.0": round(acc, 6),
            "low_conf_rows": low}


def main():
    pack = load("blind_pack.json")
    blind = load("blind_labels.json")
    res = load("t3_results.json")

    my = {row["rid"]: row for row in blind["labels"]}
    rows_out = {"recompute_labels": {}, "implementer_labels": {}}

    # ---- transcription cross-check: blind_pack vs t3_results.raw_main ----
    raw = {r["rid"]: r for r in res["raw_main"]}
    xcheck = []
    for r in pack["rows"]:
        rid = r["rid"]
        t = raw[rid]
        xcheck.append({
            "rid": rid,
            "noul_p_match": r["noul_p"] == t["noul_p"],
            "depth0_match": r["depth_score_0based"] == t["depth_score_0based"],
            "depth_conf_match": r["depth_conf"] == t["depth_conf"],
            "score_plus1_ok": abs((t["depth_score_0based"] + 1) - t["depth_score"]) < 1e-9,
        })
    rows_out["transcription_xcheck_blindpack_vs_t3results"] = xcheck

    # ---- session.jsonl mapping check: noul_p derived from decision+conf ----
    sess = [json.loads(line) for line in
            (HERE / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rid_map = {1: "R1", 2: "R1", 3: "R2", 4: "R2", 5: "R3",
               6: "R3", 7: "R4", 8: "R4", 9: "R5", 10: "R5"}
    sess_check = []
    for r in pack["rows"]:
        rid = r["rid"]
        noul_line = next(l for l in sess if l["rid"] == 2 * int(rid[1:]) - 1)
        depth_line = next(l for l in sess if l["rid"] == 2 * int(rid[1:]))
        sc = noul_line["stated_confidence"]
        dec = noul_line["decision"]
        p_derived = sc if dec == "yes" else round(1 - sc, 6)
        sess_check.append({
            "rid": rid,
            "noul_decision": dec,
            "p_derived_from_sessionlog": p_derived,
            "p_in_blindpack": r["noul_p"],
            "match": p_derived == r["noul_p"],
            "depth0_sessionlog": depth_line["decision"],
            "depth0_blindpack": r["depth_score_0based"],
            "depth_match": depth_line["decision"] == r["depth_score_0based"],
            "sessionlog_depth_stated_conf": depth_line["stated_confidence"],
        })
    rows_out["sessionlog_xcheck"] = sess_check

    # ---- step 3: metrics with MY blind labels ----
    my_noul = noul_metrics([(r["noul_p"], my[r["rid"]]["y_circ"]) for r in pack["rows"]])
    my_depth = depth_metrics(
        [(r["depth_score_0based"] + 1, my[r["rid"]]["d_depth"]) for r in pack["rows"]],
        {r["rid"]: r["depth_conf"] for r in pack["rows"]})
    rows_out["recompute_labels"]["noul"] = my_noul
    rows_out["recompute_labels"]["depth"] = my_depth

    # ---- step 4 support: implementer-label reproducibility from raw_main ----
    imp_noul = noul_metrics([(t["noul_p"], t["y_circ"]) for t in raw.values()])
    imp_depth = depth_metrics(
        [(t["depth_score_0based"] + 1, t["d_depth"]) for t in raw.values()],
        {rid: t["depth_conf"] for rid, t in raw.items()})
    rows_out["implementer_labels"]["noul"] = imp_noul
    rows_out["implementer_labels"]["depth"] = imp_depth
    rows_out["implementer_reported"] = res["metrics_main"]

    # ---- control batch (jev-latest) with my labels, comparison only ----
    lat = {t["rid"]: t for t in res["raw_latest"]}
    lat_noul = noul_metrics([(t["noul_p"], my[rid]["y_circ"]) for rid, t in lat.items()])
    lat_depth = depth_metrics(
        [(t["depth_score_0based"] + 1, my[rid]["d_depth"]) for rid, t in lat.items()],
        {rid: t["depth_conf"] for rid, t in lat.items()})
    rows_out["control_batch_with_recompute_labels"] = {"noul": lat_noul, "depth": lat_depth}

    out = HERE / "recompute_numbers.json"
    out.write_text(json.dumps(rows_out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rows_out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
