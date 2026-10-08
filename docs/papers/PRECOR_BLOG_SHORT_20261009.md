# 博客短版:We quantized our AI judge. Here's exactly what broke.(开业周首发 · R382)

> PRECOR 短文 v1.0 的博客摘编版(决策卡 R374 拍板 c·双轨第一轨):短版带判读服务 CTA;全文随后上 arXiv。风格=工程师口吻,负结果原样,零营销腔。

---

## We quantized our AI judge. Here's exactly what broke.

Our production judge — a small 1.7B model with a LoRA adapter that grades other
AI outputs as **pass / fail / insufficient_evidence** (88.5% accuracy, ECE 0.072) —
is cheap to run. The obvious next step was quantization: serve it in int8 or int4
and cut the serving cost further.

Before flipping the switch, we did something unfashionable: we **froze the
acceptance criteria first** — "a quantized judge may ship only if it agrees with
the bf16 anchor on **≥99% of 291 held-out cases**" — and published them before
looking at any number.

**Results (all measured, artifacts sha-anchored):**

| Precision | Agreement with bf16 | Verdict |
|---|---|---|
| fp16 | **100.00%** (0 flips) | ✅ ships |
| int8-nf4 | 98.28% (2 flips) | ❌ fails the gate |
| int4-nf4 | 94.16% (17 flips) | ❌ fails the gate |

Drift grows monotonically with quantization strength. The two int8 flips and
seventeen int4 flips are each a case where the judge changed its *verdict* —
not its confidence, its answer. In a self-improving training loop, a judge flip
is not a leaderboard wobble; **it is wrong training data, injected silently.**

## The four-rule deployment discipline

1. **bf16/fp16 only** for production judges — int8/int4 are off the table until
   re-certified against a new frozen gate.
2. **Freeze criteria before running.** Criteria may only move stricter; loosening
   means a fresh preregistration.
3. **Label every claim** measured / inferred / unverifiable — and publish the
   unverifiable ones anyway.
4. **Two-way judging records**: judges grade, and get graded; errata ship as
   first-class artifacts.

## The full study

Complete per-case judgment matrix, gating criteria, runner, and the pre-registered
protocol: `nautilus-compass` on GitHub and Hugging Face. The arXiv version ships
this week.

---

**Need an independent judge for your own benchmark?** Our judging lane is free:
preregistered criteria, three-state verdicts, every artifact recomputable.
Intake opens 2026-10-12 → **nautilus.social/intake.html**
· live example: nautilus.social/leaderboard.html

*Chunxiao — nautilus-compass, Nautilus Platform*

---

## 发布 checklist(开业周执行)

1. 平台博客管道排版(CTA 链接核对三连:intake/leaderboard/HF 全 200);
2. 发布时点:开业周首工作日 21:00 北京(对外发布惯例);
3. 1-2h 盯评论(dev.to 惯例);arXiv 版同周投(copyright 栏选 arXiv 非独占);
4. 发布后回链:判据档 sha+HF 模型卡互锚(#1138 式)。
