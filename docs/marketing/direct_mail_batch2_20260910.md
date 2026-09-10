# 直邮第二批草稿(9/10 拟,待用户过目)

> 目标 2 人,均个性化、无群发腔。深夜不投,明早(9/11 9-10 点)经 Gmail API 发,或用户回「发」即发。

---

## ① Di Wu(LongMemEval / LME-V2 一作,UCLA→Google Cloud AI Research)

- To: xiaowu200031@gmail.com
- 台账:无往来(首次触达);他维护 awesome-long-term-memory reading list;仓内 ATTRIBUTION.md 已明确 LME-V2 451 题归属其官方基准
- 切入:基准作者礼节性告知 + 判分卫生实证(judge 断连 14.2% 静默错判)对他的 V2 judging 协议有参考价值

**Subject:** Your benchmarks, now with sealed receipts — a judging-hygiene finding you might find useful

Hi Di,

I'm the solo dev behind nautilus-compass, an open-source agent memory layer. Your benchmarks have been the backbone of our evaluation work — LongMemEval-S (full 500) for retrieval and e2e, and the LME-V2 451-question set (attributed to your official release in our ATTRIBUTION.md).

Two things you might find useful:

1. Every number we publish now ships as a sealed pack — sha256 manifest, claims recomputable from payload bytes, ed25519-signed receipt. On your benchmark specifically: 8/8 claims recompute from bytes (summary-layer e2e 0.754 all-judged / 0.700 conservative, full 500):

    git clone https://github.com/chunxiaoxx/nautilus-compass && cd nautilus-compass
    python -m tools.verifypack verify runtime/verifypack/arma_summary/pack

2. A judging-hygiene finding: our judge gateway failed silently five times; one outage recorded 14.2% of questions as *wrong answers* while the true cause was infrastructure. We now re-judge all outage-affected questions with retry-only, disclose both accountings side by side, and deliberately do not seal any figure that can't recompute from pack-internal bytes. Protocol details: docs/REPRODUCIBILITY_WALL.md. Since LME-V2's judging protocol matters to you, this failure mode (judge-side outages masquerading as model failures) might be worth a line in your threat model.

No ask, really — if the sealed-receipt approach or the judge-outage taxonomy is ever useful to your benchmark work, glad to go deeper. And if you ever re-run anything of ours and sign the receipt with your own key, you'd be the first external verifier on our wall.

— Chunxiao Wang
nautilus-compass (github.com/chunxiaoxx/nautilus-compass)

---

## ② Haitao Li(Awesome-LLMs-as-Judges 维护者,清华 IR 组)

- To: liht22@mails.tsinghua.edu.cn
- 台账:无往来(首次触达);他的 list(610★)是其 LLMs-as-Judges 综述论文官方 repo
- 切入:我们的 judge-failure 实证+卫生协议与综述主题正交;若 list 收录协议/工具类条目,欢迎考虑(paper2 在写,如实说明)

**Subject:** A field record of LLM-judge failures in the wild — maybe relevant to your Awesome-LLMs-as-Judges list

Hi Haitao,

I maintain an open-source agent memory layer (nautilus-compass), and while evaluating it we accumulated something your survey's readers might find useful: a field record of LLM-as-judge breakdowns in production-style evaluation — five failures over one project, the worst being a judge-gateway outage that silently recorded 14.2% of questions as wrong answers while the real cause was infrastructure, not the model.

We turned that into a hygiene protocol: re-judge all outage-affected questions (retry-only, same judge), disclose dual accountings side by side, and — the part I'd highlight for your list — seal every published figure into a cryptographically verifiable pack (sha256 manifest + claims recomputable from payload bytes + ed25519-signed receipt), with an explicit rule that numbers which can't recompute from bytes don't get sealed at all. Protocol: docs/REPRODUCIBILITY_WALL.md in github.com/chunxiaoxx/nautilus-compass.

A companion paper on the judge-failure taxonomy is in preparation for arXiv — I can send you the preprint when it's up if that's useful for the list.

Thanks for maintaining the survey repo; it's a genuinely useful map of this space.

— Chunxiao Wang
nautilus-compass (github.com/chunxiaoxx/nautilus-compass)

---

## 发送备注

- 与 Trajko 封(9/10 已发)合计 3 封,全部个性化,间隔自然(不同人不同钩子),无 spam 特征
- 发送管道:Gmail REST(access_token via ~/.gmail-mcp/ refresh 流,配方同 Trajko 封)
- 若 Di Wu 或 Haitao 回信:更新 community_engagement_log.md;复算请求=反剧场主尺触发,第一时间上报
