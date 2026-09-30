# Reddit 帖稿 · r/LocalLLaMA(2026-09-30 成稿待发)

> 渠道:Reddit r/LocalLLaMA(karma≥5 门槛已过——此前已发帖);风格=技术叙事,
> 社区反感营销;弹药 A 主打+B/C 佐证
> 纪律:只述事实,黑话禁用,结尾软定位

## 标题

We fact-checked an AI performance claim by clicking the "(proof)" link. There is no link.

## 正文(英文)

---

Saw a homepage recently claiming "193.6x faster, 444.6x cheaper (proof)" — the "(proof)" suffix made it look citable, so we tried to click it.

**Finding 1: it's not a link.** We checked the HTML — no href on the "(proof)" text, no /benchmarks page, no methodology doc anywhere. The /pricing page 404s.

**Finding 2: the same page contains numbers that don't match the headline.** The demo widget shows $0.013880 → $0.000081 (171x cheaper) and 8.566s → 0.114s (75x faster). Both real numbers, both impressive — neither is 444.6x or 193.6x.

**Finding 3: one claim on the page IS verifiable** — "$42 per billion tokens, 238x cheaper than [frontier model]". 42 × 238 ≈ $10/M, which matches the public list price. So it's not fraud, it's unverifiability: different comparison sets, no methodology disclosure, self-consistent arithmetic.

Which raised the question: **how much of this category runs on numbers nobody can check?**

Quick survey of the agent-memory layer (all public sources):
- A memory startup that raised $24M (TechCrunch, Oct 2025) reports "186M API calls in Q3" — self-reported
- A company that pivoted to "enterprise context governance" still quotes "94.7% accuracy" from its own homepage benchmark
- Everyone has "(proof)". Nobody has a methodology page.

Our take after doing this for a while: the fix isn't trusting harder, it's **reproducible verification** — pre-registered criteria, frozen benchmarks, third-party recompute, published errata. We're building exactly that (independent verification lab, first live target was this homepage). Happy to answer methodology questions in comments.

What's the worst "benchmark claim vs reality" gap you've found?

---

## 审阅要点(中文)

- 结构:故事钩子(点击)→三个发现→扩展到品类→软定位→互动问题(Reddit 帖尾问题提升参与)
- 数字同 X 稿,全可溯源;不指名 TypeSafe(说 "a homepage";评论被问可给链接)
- r/LocalLLaMA 规则核对:非推销区,以方法论讨论为主体,定位只一句+评论区承诺答疑
- karma 门槛:账号此前已发过 Two-簇帖,≥5 已满足
- 发帖时段:参考 dev.to 经验 21:00 北京;Reddit 美区活跃=北京早上,建议次日 9-10am 发
