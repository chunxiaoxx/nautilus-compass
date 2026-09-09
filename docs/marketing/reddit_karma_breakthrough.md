# Reddit 发帖限制破门弹药包(9/9 · 用户反馈「限制太难」)

> 三路并行:A 攒 karma(评论)·B modmail 放行·C 替代渠道先发(X thread 已备/HN §14 已备)。
> 本档=A+B 可贴件;评论纪律:只去相关热帖、只写有数据的技术评论、不带链接(养 karma 期链接是大忌)。

## A · 养 karma 三条评论(挑当日热帖贴,不带链接)

**评论 1(适用于:本地模型/RAG/长上下文讨论帖)**
> Ran into a related tradeoff benchmarking memory layers: on LongMemEval-S retrieval (500 questions), BM25+dense hybrid with simple RRF fusion beat cross-encoder reranking by ~2pt — the embedder's own ordering was already better, reranking mostly added latency. Precision mattered way more than recall padding (K=50 ≈ K=20). Cheap beats clever at the retrieval layer more often than we expected.

**评论 2(适用于:agent 框架/agent memory 讨论帖)**
> One data point on the "summarize vs store raw" debate: extraction-based memory costs an LLM call per write and loses the ability to check what was actually said later. We store verbatim + local embedding (zero LLM at write), and route intelligence to read time — question-type routing alone moved one question type from 0.20 to 1.00 P@1. Writes are free; reads are where the intelligence belongs.

**评论 3(适用于:评测/benchmark/LLM-as-judge 讨论帖)**
> The most expensive failure in our evals wasn't a bad model — it was the judge. Caught our LLM judge failing silently 5 times in one 500-question run; one gateway outage alone mislabeled 14.2% of answers as wrong and nothing crashed. Now we dual-account every number (with/without outage questions) and preregister thresholds before runs. Cross-harness numbers in this space mostly aren't comparable and nobody says so.

> 注:三条都源自本项目实测(docs/evidence/ 有日志),无链接版安全;有人追问再给 repo。
> 贴法:每条间隔 ≥1h,不同热帖,当天别超过 3 条(新号连评=shadowban 风险)。

## B · Modmail 文案(被静默过滤时用)

**收件:r/LocalLLaMA 版主(Modmail)**

> Subject: Post filtered? — open-source memory layer with reproducible head-to-head vs mem0
>
> Hi mods — I tried posting a text post yesterday evening (headline result: our open-source local memory layer beats mem0 2.0.19 on LongMemEval-S retrieval, full 500 questions, identical criteria, P@1 0.890 vs 0.774, ~$3.50 to reproduce from the repo). It looks like it may have been auto-filtered — my account is fairly new to posting here though I've been reading the sub for a while.
>
> The post is a long technical writeup with the benchmark table, the design reasoning (zero LLM calls at write time), our failed experiments, and links only in a first comment per the sub's conventions. Happy to adjust anything — title, length, structure. If it's a karma threshold thing, I completely understand and will come back after participating more.
>
> Repo for reference: github.com/chunxiaoxx/nautilus-compass (Modified MIT, bilingual README)
>
> Thanks for the work you all do here — it's the only sub where this kind of head-to-head with receipts actually gets discussed.

## C · 替代渠道(已备,今天可发)

- X 英文 thread 7 条(v3 §B2,条 1 附 table_headtohead_en.png)
- HN:repo 直链 + §14 标题 `Nautilus-compass: Local-first agent memory – write path makes zero LLM calls`(9/10-11 原计划可提前)

## 破门后动作

发帖成功 → 贴链接给我 → reddit_watch init → 值守开始(§6 应答模板+口径卡)。
