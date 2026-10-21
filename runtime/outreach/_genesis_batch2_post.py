import json, urllib.request, os

TOKEN = os.environ["GITHUB_TOKEN"]
H = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json",
     "User-Agent": "nautilus-compass-outreach/1.0"}

TITLE = "[Offer] Free third-party verification of your memory-engine benchmark claims (Nautilus Compass)"

SIGN = """Thanks for reading — and regardless, good luck with {luck}.

— Nautilus Compass (judging & verification service · verdicts free forever, binding deliverables paid)"""

BODIES = {
"supermemoryai/supermemory": """Your "extremely fast, fully-local Memory API" pitch is exactly the kind of quantified claim buyers can't currently verify — speed and local-run numbers come from the vendor's own harness, which is how the whole category works right now.

We're Nautilus Compass: a third-party verification service for agent-memory benchmark claims. Free, permanently: pre-registered criteria, recomputed by someone who didn't write the code, every claim tagged `[measured] / [inferred] / [unverifiable]`.

If you'd like your performance claims independently recomputed and stamped on a public verdict wall, we'll do it at zero cost. Two artifacts to skim first:

- How it works (published today): https://dev.to/chunxiaoxx/who-graded-your-agents-benchmark-score-4hjj
- Live verdict wall incl. negative results & "insufficient evidence" cards: https://org.nautilus.social/results.html

Fair warning: if a number doesn't reproduce, that gets published too — that's the product. Zero obligation; a one-line reply pointing at the benchmark artifact you trust most is enough to start.

""" + SIGN.format(luck="the memory API for the AI era"),

"Mirix-AI/MIRIX": """A multi-agent assistant that tracks on-screen activity and answers questions intelligently lives or dies on memory quality — yet "intelligently" is currently graded by the team that built it, which is the norm in this category, not a knock on MIRIX.

We're Nautilus Compass: third-party verification for agent-memory benchmark claims. Free, permanently: pre-registered criteria, non-implementer recomputation, every claim tagged `[measured] / [inferred] / [unverifiable]`.

If you'd like an independent verdict card for MIRIX's memory/retrieval claims — public wall, zero cost — we'll run it. Two artifacts to skim:

- How it works (published today): https://dev.to/chunxiaoxx/who-graded-your-agents-benchmark-score-4hjj
- Live verdict wall incl. negative results: https://org.nautilus.social/results.html

Fair warning: numbers that don't reproduce get published too — that's the product. Zero obligation; a one-line reply with the benchmark artifact you trust most starts it.

""" + SIGN.format(luck="MIRIX"),

"getzep/zep": """Knowledge-graph memory (Graphiti lineage) makes some of the strongest structural claims in the agent-memory space — and like the rest of the category, they're currently self-graded.

We're Nautilus Compass: third-party verification for agent-memory benchmark claims. Free, permanently: pre-registered criteria, recomputed by a non-implementer, every claim tagged `[measured] / [inferred] / [unverifiable]`.

If you'd like Zep's retrieval/accuracy claims independently recomputed onto a public verdict card — zero cost, zero obligation — we'll run it. Two artifacts to skim:

- How it works (published today): https://dev.to/chunxiaoxx/who-graded-your-agents-benchmark-score-4hjj
- Live verdict wall incl. negative results & insufficient-evidence cards: https://org.nautilus.social/results.html

Fair warning: numbers that don't reproduce get published too — that's what makes the stamp worth anything. A one-line reply pointing at your benchmark artifact starts it.

""" + SIGN.format(luck="Zep and Graphiti"),

"MemTensor/MemOS": """"35.24% token savings" is exactly the kind of quantified, falsifiable claim this industry needs more of — and exactly the kind an independent party can verify. Right now it's graded by its authors, which is the category norm, not a knock on MemOS.

We're Nautilus Compass: third-party verification for agent-memory benchmark claims. Free, permanently: pre-registered criteria, recomputed by a non-implementer, every claim tagged `[measured] / [inferred] / [unverifiable]`.

We'd gladly run the 35.24% savings claim (and any retrieval numbers) through independent recomputation onto a public verdict card — zero cost. Two artifacts to skim:

- How it works (published today): https://dev.to/chunxiaoxx/who-graded-your-agents-benchmark-score-4hjj
- Live verdict wall incl. negative results: https://org.nautilus.social/results.html

Fair warning: numbers that don't reproduce get published too — that's the product. A one-line reply with the eval artifact behind the savings number starts it.

""" + SIGN.format(luck="MemOS"),
}

for repo, body in BODIES.items():
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues",
        data=json.dumps({"title": TITLE, "body": body}).encode(), headers=H, method="POST")
    try:
        r = json.load(urllib.request.urlopen(req, timeout=30))
        print(f"OK {repo}#{r.get('number')} | {r.get('html_url')}")
    except Exception as e:
        detail = getattr(e, "read", lambda: b"")()[:150] if hasattr(e, "read") else ""
        print(f"FAIL {repo}: {e} {detail}")
