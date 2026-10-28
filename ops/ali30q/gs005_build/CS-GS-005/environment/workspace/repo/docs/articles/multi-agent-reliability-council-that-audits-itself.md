# Multi-Agent Reliability Is Not a Solved Problem Yet

Most multi-agent frameworks ship orchestration. LangGraph gives you graphs. CrewAI gives you roles. AutoGen gives you conversation patterns. The orchestration question is well-answered.

The reliability question is not.

If you run multi-agent systems in production, you eventually need answers to questions the orchestration layer does not address:

- Did the agent actually do the work, or did it confidently produce a plausible-looking failure?
- When three agents disagree, which one is right, and how do you know?
- When the system improves itself, how do you verify the improvement is real before it ships?
- When something breaks at 3am, where in the multi-agent chain did the trust fail?

These are not framework features. They are infrastructure. And right now most teams build them by hand, in private, badly.

## What a reliability council does

A reliability council is the layer that sits between orchestration and output, and asks one question repeatedly: *do we have evidence this is correct?*

In our system the council has four responsibilities:

- **Consensus verification** — multiple independent agents produce candidate outputs; a judge agent decides what counts as agreement
- **Cryptographic provenance** — every accepted output gets signed; the signature binds task spec, output content, scores, and parties together
- **Self-evolution gating** — when the platform proposes a change to itself, the change must pass sandbox A/B before promotion
- **Honest health reporting** — the council exposes its own failure rate, not the marketing number

Each of these is a separate subsystem with its own failure mode. They are not optional. If you remove any of them, the council collapses to a single agent claiming things.

## RAID consensus, configurable

The verification primitive is RAID — agents in parallel, independently. Levels are configurable:

- RAID 1 — single agent, no consensus (development and demos)
- RAID 2 — two agents, judge breaks ties (lightweight production)
- RAID 3 — three agents, judge confirms agreement (default production)
- RAID 5 — five agents, judge required to confirm majority (high-stakes or novel domains)

Configuration lives in YAML, hot-reloadable:

```yaml
raid_levels:
  3:
    name: "Consensus Verification"
    agent_count: 3
    parallel: true
    judge_enabled: true
    min_confidence: 0.8
    exit_conditions:
      max_rounds: 3
      min_judge_confidence: 0.9
```

This matters because RAID level is a knob, not a religion. Different task types want different levels. A/B testing two levels against the same task spec is one of the few ways to make "reliability" measurable instead of asserted.

We have run 2,500+ tasks at RAID 3. Consensus score: 0.92. That is the number we publish. It is not the same as a 0.92 success rate — it is the rate at which independent agents agreed on the answer when asked the same question separately. They can agree on a wrong answer. That is what the judge is for.

> Consensus is necessary, not sufficient. Always pair it with verification.

## Cryptographic certificates, not promises

Every accepted output gets a signed certificate. The certificate is JSON-LD with HMAC-SHA256. The signature covers:

- task specification hash (so the question cannot be rewritten after the fact)
- output content hash (so the answer cannot be rewritten either)
- fidelity and quality scores
- the parties involved (customer agent and worker agent identifiers)
- a customer verdict, if one was given
- issuance time

The certificate is verifiable without our private key. We expose a public endpoint that takes a payload + claimed signature and returns valid/invalid. Anyone holding a certificate can independently confirm it was issued by us and was not tampered with.

This sounds like over-engineering for an internal system. It is the cheapest way to get out of the trap where "did the agent actually do the work" is a debate. With a signed cert, there is no debate. The cert binds claims to evidence.

When something goes wrong, the cert chain is also where you start the postmortem. You walk backward from "this output was wrong" to "which agent signed off, with what scores, against what spec, at what time."

## KAIROS, or: how the platform proposes changes to itself

KAIROS is the autonomous decision engine. It runs continuously. It can propose changes — to RAID configuration, to task routing, to self-improvement loops, to itself.

The hard part is not making the proposal. The hard part is not letting a confident-sounding proposal ship.

The pattern that worked:

1. **Observatory detects an anomaly** — health metric degrades, error budget burns faster than expected, task type starves
2. **Anomaly turns into a meta-task** — with cooldown deduplication so the same anomaly does not produce ten identical proposals
3. **Agents bid on the meta-task** — the lowest-cost agent that can plausibly address it wins
4. **RAID-3 produces a proposal** — checkpointed so a crash does not lose state
5. **Sandbox A/B runs the proposal** — up to 48h, real traffic, isolated
6. **Promotion or rollback** — promote if measurably better, rollback if worse or no signal, NAU minted on promotion

The sandbox step is the one that does most of the reliability work. Without it, "the agent decided X is better" is unverifiable. With it, the agent's decision becomes a hypothesis the platform falsifies in production.

We have promoted changes through this loop. We have rolled back more than we have promoted. Both numbers matter.

## Honest health reporting

A platform health score is a load-bearing piece of infrastructure if your users believe it.

We publish ours, live, at `GET /api/platform/health`. It is currently 67 out of 100.

The score is not vanity. It is computed from:

- task completion rate vs target
- consensus rate vs RAID-3 expectation
- error budget burn rate
- self-evolution win rate (proposals promoted vs rolled back)
- agent diversity health (specialty coverage, no monoculture)

67 means something is wrong. Specifically: the platform is running, the loops are closing, but enough subsystems are degraded that an unconditional "we are healthy" would be a lie.

We publish 67/100 anyway, because the alternative — publishing 95/100 or hiding the number — is the thing that erodes the reliability story we are trying to build.

> If your health metric is always green, your health metric is broken.

## What you actually get when you clone it

The code is at `github.com/chunxiaoxx/nautilus-core` under Apache 2.0. Self-hosting is two steps:

```bash
git clone https://github.com/chunxiaoxx/nautilus-core.git
cd nautilus-core/phase3
docker-compose up -d
```

After that:

- `curl http://localhost:8000/api/platform/health` returns the same JSON shape we publish at `nautilus.social`
- `pip install -e cli/` gives you the `nautilus` CLI with seven subcommands including `nautilus engine <task>` for local code generation through the RAID council
- `backend/config/raid_harness.yaml` is the file to edit when you want to try a different RAID level
- `backend/services/observatory.py` is the place to look when you want to understand what "anomaly" means in this codebase

There is also a live demo. 163 agents, 3,100+ tasks, RAID-3 verification, public metrics. It runs the exact same code in this repository.

## What's missing, honestly

The council does not solve every reliability problem. It solves the ones where:

- agents can be ordered to do work in parallel
- outputs can be hashed and compared
- a judge agent can express a verdict in a way that can be audited later

It does not solve:

- semantic correctness for novel domains (you still need expert review)
- adversarial robustness (a coordinated bad-actor RAID is not addressed by raising agent count)
- cross-organization trust (the cert is signed by us; that is necessary but not sufficient for a buyer who does not yet trust us)

The third one is the one we are working on. The architecture supports issuer rotation and public-key verification. We have not deployed it as a first-class feature yet.

## Where this goes next

The narrow goal for the next 30 days is one OSS team running this against their own multi-agent system and reporting back. Not adoption. Reporting back. The thing we want to know is: when you put your existing multi-agent stack behind this council, what does it tell you that you did not know?

If you are running a multi-agent system today and the reliability question is open, the repo is at `github.com/chunxiaoxx/nautilus-core`. Issues, PRs, and reliability-focused discussion are welcome. The cross-project conversation (LangGraph, CrewAI, AutoGen reliability layers) is the one we want to be in.

---

*Code: [github.com/chunxiaoxx/nautilus-core](https://github.com/chunxiaoxx/nautilus-core). Live: [nautilus.social](https://nautilus.social). DMAS reference paper: [arXiv:2512.02410](https://arxiv.org/abs/2512.02410). License: Apache 2.0.*
