# r/MachineLearning 论文贴模板(等 arXiv ID,24h 内发)

> 版规要点(r/ML):标题=论文标题原样(不加营销语);正文或首评必须以论文为中心;
> repo 链接可放但不做首句导流;严禁拉票。发布账号 chunxiaoxx。
> 数字口径全部取自 SCOREBOARD 定案;术语 judge hygiene 全文使用(lexicon_20260905)。

---

## 标题(=论文标题原样)

```
Judge Failure in the Wild: A Taxonomy of LLM-as-Judge Breakdown and a Hygiene Protocol for Long-Memory Evaluation
```

## 首评(发布后立即贴,~220 词)

> I'm the author. Short version of why this paper exists:
>
> Our production long-memory eval caught its own LLM judge failing — three
> structurally distinct ways. Not biases to be corrected, but breakdowns:
> **knowledge-boundary blindness** (judges can't represent ±0.1% score
> perturbations; pass rates 37–48% even when explicitly instructed),
> **budget blindness** (reasoning silently consumes the output budget before
> any verdict), and **connectivity blindness** (an infra outage recorded
> 14.2% of items as wrong answers, moving headline accuracy by 5.4 points on
> an effect of 32.8).
>
> The three types differ on every axis that matters — detectable signal,
> whether retry cures them, whether they're catchable pre-deployment — so
> conflating them produces wrong responses. We contribute the taxonomy from
> 2,600 controlled API calls plus two production incidents, and a five-item
> **judge hygiene** protocol (preregistered gates; same-judge retry backoff;
> three-caliber disclosure; deployment smoke; binomial noise bands). The
> protocol resolved 71/71 disconnect-mislabeled items in place.
>
> The uncomfortable generalization: if your benchmark uses an LLM judge and
> you haven't audited the judge itself, your leaderboard measures your judge
> as much as your systems. Happy to answer questions about the perturbation
> methodology.
>
> Paper: https://arxiv.org/abs/{ARXIV_ID} · Protocol and checklist:
> [PROTOCOL link / repo]

## 发布记录(发出后回填)

| 项 | 值 |
|---|---|
| arXiv ID | _待回填_ |
| 发帖时间 | _待回填_(北京 21-24 点=美东上午窗口) |
| 24h 数据 | _待回填_ |

## 应答预案

- **"样本就 2600 个调用,能说明什么?"**:承认规模有限;强调三类失败的*结构性*区别与生产事故的复现一致性;欢迎他人在各自 harness 复测(checklist 公开)。
- **"这不是早就有人知道吗"**:bias 文献确实大量存在;本文贡献是把*静默 breakdown* 与 *bias* 区分开并给出可执行 checklist——audit 表在 §5。
- **"你们自己请的判官还有脸说别人"**:这正是论文立场——我们从自己的 5 次事故出发(两起写入正文),不指控任何第三方榜单;协议公开欢迎复用。
