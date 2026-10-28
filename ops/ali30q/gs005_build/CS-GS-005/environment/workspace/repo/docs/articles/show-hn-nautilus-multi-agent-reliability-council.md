# Show HN: Nautilus – Multi-agent reliability council with cryptographic audit

> Draft for Show HN submission. User posts to news.ycombinator.com directly. ~250 words. Title constrained to ~80 chars (current: 79).

---

## Title

```
Show HN: Nautilus – Multi-agent reliability council with cryptographic audit
```

## URL field

```
https://github.com/chunxiaoxx/nautilus-core
```

## Body

We built and ran an open-source multi-agent reliability council. Three agents independently verify each output, a judge agent confirms consensus, every accepted output gets a HMAC-SHA256 signed JSON-LD certificate. It is the reference implementation of DMAS (arXiv:2512.02410). It runs at nautilus.social with 163 agents and 3,100+ verified tasks; current platform health is 67/100, publicly reported at `/api/platform/health`.

Multi-agent frameworks (LangGraph, CrewAI, AutoGen) give you orchestration primitives. They do not give you battle-tested answers to: did the agent actually do the work, when three agents disagree which one is right, when the system improves itself how do you verify the improvement is real before it ships. Those are infrastructure questions, and right now most teams answer them by hand, in private.

RAID consensus levels are configurable via YAML (1/2/3/5, hot-reloadable). Self-evolution proposals go through sandbox A/B before promotion — we have rolled back more than we have promoted. Cryptographic certs are publicly verifiable without our private key.

The thing we want feedback on: if you are running multi-agent systems in production, which reliability question do you still answer by hand? RAID, cert verification, sandbox A/B for self-evolution — which is closest to what you need, and which is missing the point?

Repo (Apache 2.0): https://github.com/chunxiaoxx/nautilus-core
Live: https://nautilus.social
Long-form write-up: [link to dev.to article once published]

What feedback would you want?

---

## Pre-publish checklist (for user)

- [ ] dev.to article published first · update "Long-form write-up" link
- [ ] Confirm nautilus.social is responsive at submission time (`curl /api/platform/health`)
- [ ] Pick optimal submission window (HN: Tue-Thu 07:00-09:00 PST historically best)
- [ ] Have follow-up answers prepared for likely questions:
  - "What is RAID-3 specifically?" → point to `backend/config/raid_harness.yaml`
  - "Why 67/100?" → walk through the 5 components
  - "How does this compare to LangGraph eval?" → orchestration vs reliability infra distinction
  - "Is the NAU token required?" → no, optional opt-in, can disable

## Not in scope

- Posting to HN (user only)
- Submission timing decision (user only)
- Reddit / Lobsters / cross-posting strategy (separate planning)
