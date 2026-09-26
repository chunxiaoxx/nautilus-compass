# Jev 校准证据 · 对外材料(2026-09-26 · 供用户直发)

> 用途:直接复制英文正文发出(X/Discord/社区皆可);中文备用段在尾。
> 纪律:只谈我们实测的校准读数;"快/便宜"是 TypeSafe 官方宣称,不在此
> 越权引用。部分读数标注待独立复算——如实保留,这是可信度本身。

---

## 英文正文(复制即发)

We tested Jev 1.13.0's claimed "calibrated confidence" on our own domains.
Not on their benchmark — on ours. All artifacts public, grader re-runnable.

Headline number: on a synthetic email triage task (3-class choice),
**Jev stated 91% confidence and was right 50% of the time.**
Calibration score C (= 1 − ECE): 0.086.

Full domain sweep (same instrument, jev-trust, n=120 per domain):

| Domain | Accuracy | Confidence | C (1−ECE) |
|---|---|---|---|
| Closed deterministic tasks | — | — | 0.959 |
| Adversarial stress | — | — | 0.988 |
| Python exception prediction | 100% | — | 0.953 |
| Code-patch behavior verdicts | 92.5% | — | 0.866 |
| Embodied-data QC labeling | 50% (all-yes strategy) | — | **0.689** |
| Email triage (boolean spam) | — | — | 0.831 |
| Email triage (3-class choice) | **50%** | **91%** | **0.086** |

The pattern: **calibration collapses exactly where the domain is fuzzy and
the stakes are operational** (triage, labeling, behavioral judgment) — and
holds where tasks are closed-form. Jev is a fast, cheap decision engine;
just don't read its confidence at face value in your domain until you've
measured it on your data.

Disclosure: rows 3–5 await independent recompute by a second operator
(marking in the directory); rows 1–2 and 6–7 single-run. Nautilus's own
memory system is listed UNVERIFIED on the same wall — same ruler for
ourselves.

How to check us:
- Live directory (signed scorecards, methodology):
  https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/wall/MEMORY_SYSTEMS_DIRECTORY.md
- Instrument (pip install jev-trust, MIT): https://pypi.org/project/jev-trust/
- Trust Report #1: https://compass.nautilus.social/trust_report_2026-09.html

If you run Jev in production, we'll calibrate it on 20–50 of your real
decisions and hand you a signed report with an actionable confidence
discount ("treat 0.9 as 0.77 in your domain"). That's the product.

---

## 中文备用(发中文平台时用)

我们用自己的域测了 Jev 1.13.0 标榜的「校准置信度」。不是用它家的
基准,是用我们自己的。全部工件公开、判分可复跑。

最刺眼的数字:合成邮件三分类任务上,**Jev 自报置信 91%,实际正确率
50%**,校准分 C(=1−ECE)只有 0.086。

七个域扫下来规律很清楚:**域越模糊、越是业务场景(分诊/标注/行为
判断),校准崩得越狠;闭合式任务上倒是不错。**Jev 是快而省的决策
引擎,但在你的域里,它的置信度别按面值用——先在你自己的数据上量过
再说。

诚实披露:第 3-5 行读数待第二操作员独立复算(目录里标着);我们自家
记忆系统在同一面墙上挂的是 UNVERIFIED——同一把尺子量自己。

查我们:
- 验证墙(签名成绩单+方法论):
  https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/wall/MEMORY_SYSTEMS_DIRECTORY.md
- 测量仪器(MIT,pip install jev-trust):https://pypi.org/project/jev-trust/
- Trust Report #1:https://compass.nautilus.social/trust_report_2026-09.html

如果你在生产环境跑 Jev:给我们 20-50 条你的真实决策样本,48 小时还你
一份带签名的域校准报告,附一句可操作的话——「你的域里 0.9 的置信
当 0.77 用」。这就是我们的产品(DCR 域校准报告)。
