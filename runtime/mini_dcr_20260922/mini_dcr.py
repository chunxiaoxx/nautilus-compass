"""mini-DCR dry-run: full fulfillment chain in 15 min (20 q, one synthetic business domain)."""
import json, random, time, urllib.request, hashlib, sys
from pathlib import Path
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "mini_dcr"
OUT.mkdir(parents=True, exist_ok=True)
key = (Path.home() / ".claude" / ".cache" / "typesafe_api_key.env").read_text(encoding="utf-8").strip().split("=", 1)[1]
rng = random.Random(20260922)
DOM = "email triage: urgent / normal / archive (3-way) + spam bool"
qs = []
labels = ["urgent", "normal", "archive"]
for i in range(10):
    sender = rng.choice(["ceo@company.com", "noreply@ads.com", "hr@company.com", "random@spam.io"])
    subj = rng.choice(["server down", "50% off!!!", "payroll reminder", "you won a prize"])
    spam = sender.endswith(("ads.com", "spam.io")) or subj in ("50% off!!!", "you won a prize")
    qs.append({"qid": f"s-{i:02d}", "kind": "noul", "state": {"from": sender, "subject": subj, "body_words": rng.randint(5, 200)},
               "q": {"type": "noul", "instructions": "Is this email unsolicited advertising or a scam attempt? (spam=true)"}, "truth": 1 if spam else 0})
for i in range(10):
    sender = rng.choice(["ceo@company.com", "noreply@ads.com", "hr@company.com"])
    subj = rng.choice(["server down", "50% off!!!", "payroll reminder"])
    urgent = subj == "server down" and sender == "ceo@company.com"
    lbl = "urgent" if urgent else ("normal" if sender == "hr@company.com" else "archive")
    qs.append({"qid": f"c-{i:02d}", "kind": "choice", "state": {"from": sender, "subject": subj},
               "q": {"type": "choice", "instructions": "Classify this email into exactly one bucket.",
                     "criteria": {"u": "urgent", "n": "normal", "a": "archive"}}, "truth": {"urgent": "u", "normal": "n", "archive": "a"}[lbl]})
(OUT / "mini_set.json").write_text(json.dumps(qs, sort_keys=True), encoding="utf-8", newline="\n")
results = []
for item in qs:
    body = json.dumps({"model": "jev-latest", "state": item["state"], "questions": {"q": item["q"]}}).encode()
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=body, method="POST",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        results.append({"qid": item["qid"], "kind": item["kind"], "truth": item["truth"], "answer": r["answers"]["q"]})
    except Exception as e:
        results.append({"qid": item["qid"], "kind": item["kind"], "truth": item["truth"], "error": str(e)[:150]})
    time.sleep(0.3)
(OUT / "mini_raw.jsonl").write_text("\n".join(json.dumps(x, sort_keys=True) for x in results), encoding="utf-8", newline="\n")
noul = [(r["truth"], float(r["answer"]["noul"])) for r in results if r["kind"] == "noul" and "answer" in r and isinstance(r["answer"].get("noul"), (int, float))]
choice = [r for r in results if r["kind"] == "choice" and "answer" in r]
acc_b = sum(1 for t, p in noul if (p >= .5) == (t == 1)) / len(noul)
brier_b = sum((p - t) ** 2 for t, p in noul) / len(noul)
def ece(prs):
    e = 0
    for b in range(10):
        lo, hi = b/10, (b+1)/10
        g = [(p, t) for p, t in prs if lo <= max(p, 1-p) < hi or (b == 9 and max(p, 1-p) >= .999)]
        if g: e += len(g)/len(prs) * abs(sum(max(p,1-p) for p,_ in g)/len(g) - sum(1 for p,t in g if (p>=.5)==(t==1))/len(g))
    return e
acc_c = sum(1 for r in choice if r["answer"].get("choice") == r["truth"]) / len(choice) if choice else None
conf_c = sum(max(r["answer"]["probabilities"].values()) for r in choice if r["answer"].get("probabilities")) / len(choice) if choice else None
print(json.dumps({"domain": DOM, "n_noul": len(noul), "noul_acc": round(acc_b,4), "noul_brier": round(brier_b,4),
                  "noul_ece": round(ece([(p,t) for t,p in noul]),4),
                  "n_choice": len(choice), "choice_acc": acc_c, "choice_avg_conf": conf_c}, ensure_ascii=False))
