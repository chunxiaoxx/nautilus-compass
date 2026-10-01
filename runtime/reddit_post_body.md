We built a 30-question exam testing whether AI agents can remember their own operational history. The first thing it caught was **us** — our grader was wrong on 7 of 18 items, including two wrong answer keys.

## The experiment

We ran a controlled three-arm experiment: same backbone (MiniMax-M3), same questions, only the memory path changed:

- Direct access: **16/18**
- Through mem0 (default, semantic compression on): **11/18**  
- Through mem0 (compression off): **18/18**

One config flag = 7 points. The compression drops machine-checkable fields (`artifact: null`) that audits need.

## The TypeSafe recompute

TypeSafe's homepage says their model Jev is "193.6x Faster, 444.6x Cheaper (proof)." We put that through our recompute protocol:

1. **Claims are self-consistent** with their published evals: 444.6x matches vs opus 5 (we compute 440.1x), 193.6x tracks vs sonnet 5 (183.8x)

2. **Our independent benchmark** (90 timed calls): Jev at flat 0.44-0.48s latency, vs MiniMax-M2.7 at 3.7-12.8s — ratio of **7.9-18.2x**, not 193.6x

3. **The multiplier landscape is two clusters**: every fast cheap model lands in a narrow 16-18x band; heavy generators sit at 184-440x

> A single headline number is marketing. The multiplier-vs-comparison curve is the information.

## Why this matters

Every vendor ships scorecards; none ships the grader. Consumers can't draw the comparison curve from a homepage — they need someone to run it.

Full artifacts + recompute scripts: https://github.com/chunxiaoxx/nautilus-compass

*(This is from Assay — an independent AI verification lab. We test AI agents' memory and recompute vendor claims.)*
