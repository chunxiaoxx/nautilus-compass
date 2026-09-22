import json, urllib.request, time
from pathlib import Path
key = (Path.home() / ".claude" / ".cache" / "typesafe_api_key.env").read_text(encoding="utf-8").strip().split("=", 1)[1]
API = "https://api.typesafe.ai/v1/systemone"
papers = [
    {"qid": "0616", "truth": "agree", "d": "Function-level fix to genopt dispatch, adds routing logic. 5 tests passed."},
    {"qid": "6f1e", "truth": "agree", "d": "Adds build_swe_fix_prompt with extract_fixed_file. 28 tests passed after import fix."},
    {"qid": "28c2", "truth": "disagree", "d": "Modifies feishu schema validation. 18 tests failed out of 97."},
    {"qid": "71f0", "truth": "nc", "d": "SQLite persistence for flywheel events. Tests import missing dependency module."},
    {"qid": "914b", "truth": "agree", "d": "Core repo fix, all 72 tests passed first attempt."},
    {"qid": "0c2c", "truth": "agree", "d": "Retake after fixing corrupt patch, 13 tests passed."},
    {"qid": "37a1", "truth": "agree", "d": "Long-run pass after 148 minutes, 16 tests passed."},
    {"qid": "355a", "truth": "disagree", "d": "pass@2: import scope bug, NameError on fragment_version, wrong tuple arity."},
    {"qid": "a379", "truth": "disagree", "d": "Think-tag stripping residue causes SyntaxError in output diff."},
]
results = []
for p in papers:
    body = json.dumps({
        "model": "jev-latest",
        "state": f"Programming exam submission review. Fix description: {p['d']}",
        "questions": {"v": {"type": "choice",
            "instructions": "Predict the exam verdict: will hidden tests pass after applying this fix?",
            "criteria": {"agree": "Tests will pass - fix is correct",
                        "disagree": "Tests will fail - fix has issues",
                        "nc": "Cannot judge - missing dependencies or incomplete materials"}}}
    }).encode()
    req = urllib.request.Request(API, data=body, method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        ans = r["answers"]["v"]
        results.append({"qid": p["qid"], "truth": p["truth"], "pred": ans.get("choice"),
                       "conf": ans.get("confidence"), "probs": ans.get("probabilities", {})})
    except Exception as e:
        results.append({"qid": p["qid"], "truth": p["truth"], "error": str(e)[:120]})
    time.sleep(0.4)
ok = [r for r in results if "pred" in r]
match = sum(1 for r in ok if r["pred"] == r["truth"])
print(f"Phase 0: {match}/{len(ok)} = {match/len(ok)*100:.0f}%" if ok else "all error")
for r in results:
    p = r.get("pred", r.get("error", "?")[:40])
    m = "✓" if r.get("pred") == r["truth"] else "✗"
    print(f"  {r['qid']}  truth={r['truth']:10s}  pred={p:10s}  conf={r.get('conf','?')}  {m}")
