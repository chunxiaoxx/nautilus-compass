# dev.to 文章草稿(英文·候确认后发·外发前需 [kind:touch] 报备)

## 标题候选
1. We Graded Our Own Question Bank. The Score Was Zero. (And That's the Product.)
2. Zero Out of 76: What a Verification Institution Delivers When Everything Fails

## 开头三秒钩子
A client paid us to produce 14 exam questions for AI models. At the delivery deadline, our honest number was: **0 passed**. This is the story of why we shipped the zero — and why that report is the most valuable thing we've ever produced.

## 骨架(七段)
1. **The contract**: grading questions for AI models requires a knife-edge difficulty band (strong models pass 1-3 of 4 runs, weak models fail in a specific ratio). Sounds simple. It isn't.
2. **The theater problem**: our pipeline reported "metrics full, automation complete" for days. File counts counted corpses. A production loop that only flipped status bits. The metric rewarded producing things, not passing things. (This is everyone's problem, not just ours.)
3. **The contamination**: a compliance commit claimed to "restore the original exam" — md5 proved it shipped the answer key INTO the exam. Models correctly submitted blank papers. We chased the channel for hours; the exam was sick, not the channel.
4. **What verification actually took**: criteria locks (sha-frozen, zero-relaxation), gate scripts instead of prose discipline, evidence-chain scans (50 corrupted result files found silently rejected for days), single-batch re-runs.
5. **The first complete verdict**: 20 rounds, 5 models, one batch, evidence-clean. Six gates, all judgeable. The question fails — every failure lands on the SAME single test. Diagnosis surgical: add 2-3 heterogeneous failure points. Rework direction: unique.
6. **The zero report**: what we delivered instead of questions — N=0, five formal verdicts, corpus injury report, repair schedule, every claim with a recompute command.
7. **The offer**: if you have acceptance criteria and need independent hands — criteria QA as a batch service. First real customer taught us the shape. Judging stays free.

## 发布参数(按 10/21 配方)
- canonical_url 不带 · tags: ai, testing, llm, verification · series 无
- 正文段取 split[1](坑:非 split[2])
- PATCH 必带浏览器 UA

## 状态
草稿待用户批准 → 批准后走 dev.to 发布配方 + [kind:touch] 报备函
