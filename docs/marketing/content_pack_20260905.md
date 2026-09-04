# 传播内容包 v1(2026-09-05)——供 agent 对话框执行

> 分工拍板(用户 9/5):compass 框负责生成制作全部素材;agent 对话框负责持续传播推广执行。
> 本文件=agent 执行工作包:纪律+素材索引+短格式文案全文。数字一律以
> `docs/nautilusmem/SCOREBOARD.md` 定案口径为准,**禁止任何改写**。

## 0. 执行纪律(每轮必读)

1. **所有对外发布动作必须用户排期拍板后执行**;agent 只准备弹药,不自行扣扳机。
2. 不买量、不刷票、不用小号、不冒充用户;被质疑只对事实不对人,答不上来说 open question。
3. 每渠道一条素材只发一次,不复读;评论区 24h 内值守,技术性回复 3-5 条/帖即止。
4. 发布记录(时间/链接/首日数据)回填本文件 §8,供复盘。

## 1. 素材总索引

| 渠道 | 层 | 素材 | 状态 |
|---|---|---|---|
| r/LocalLLaMA 主帖+首评 | ① | [20260904_launch_post_v3.md](20260904_launch_post_v3.md) + launch_plan §13 | ✅ |
| X thread 7 条 | ① | launch_post_v3 内嵌 | ✅ |
| HN 标题+首评 | ① | launch_plan §14 | ✅ |
| 架构立场长文(~1900 词) | ① | [20260904_architecture_position_paper.md](20260904_architecture_position_paper.md) | ✅ |
| 第二篇(判分卫生) | ① | 8c5bc78 成品 | ✅ |
| Bluesky/Mastodon/Lobsters/Newsletter/MCP 社区 | ① | **本文件 §2-§6** | ✅ |
| 演讲 PPT(12 页+讲者注) | 材料 | pitch_deck_20260904.pptx/.html | ✅ |
| demo 录屏脚本 | 材料 | [demo_recording_script.md](demo_recording_script.md) | ✅ 待用户录 |
| 中文圈三件(知乎/公众号/V2EX) | ② | ✅ 成品 v1:[知乎答](zh_zhihu_answer_20260905.md) / [公众号文](zh_wechat_tech_20260905.md) / [V2EX 帖](zh_v2ex_share_20260905.md),重写非搬运,发布 9/15 周 |
| r/MachineLearning 论文贴 | ① | ⏸ 等 paper2 arXiv ID | — |

## 2. Bluesky(每条 ≤300 字符,连发)

**P1**
> Write-time compression is a blind bet on the future. Our agent memory stores verbatim — zero LLM at write, local BGE-m3 — and puts all intelligence in read-path routing. LongMemEval-S e2e: 42.6% → 75.4%. #LocalLLM #MCP #AgentMemory

**P2(接 P1)**
> Same 500 questions, same criteria, same embedder vs our mem0 reproduction: retrieval P@1 0.890 vs 0.774. ~$3.50 to re-run — scripts in repo. Modified MIT: self-host free forever. github.com/chunxiaoxx/nautilus-compass

## 3. Mastodon(单条 ≤500 字符)

> nautilus-compass: local-first agent memory. Write path = verbatim storage, zero LLM calls, local BGE-m3, nothing leaves your machine. Read path = query-type routing: LongMemEval-S e2e 42.6%→75.4% (dual accounting, judge outages disclosed). Head-to-head vs our mem0 reproduction — same questions, same criteria: P@1 0.890 vs 0.774, ~$3.50 to reproduce. Modified MIT, self-hosting free forever. https://github.com/chunxiaoxx/nautilus-compass

## 4. Lobsters(title+首评)

**Title**:`nautilus-compass: local-first agent memory — the write path makes zero LLM calls`

**首评(submitter comment)**
> The design bet: nobody knows at write time what will be asked later, so compression/extraction at write is a wager you structurally lose. This stores observations verbatim (local BGE-m3 embeddings, SQLite) and concentrates all intelligence at read time — query-type routing, BM25+dense RRF fusion, date anchoring, summary-card assembly. On LongMemEval-S the routing lifts e2e from 42.6% to 75.4%, with dual accounting (81.6% excluding 71 judge-outage questions — disclosed). Same-questions-same-criteria head-to-head vs our mem0 2.0.19 reproduction: P@1 0.890 vs 0.774; reproduction ≈$3.50 GPU-time, scripts in repo. Solo dev, 130 days; my own agent fleet wrote most commits — the org runs on it (dogfood). License is Modified MIT (trademark + hosted-paying-user cap; self-hosting free forever). Happy to dig into the routing design.

## 5. Newsletter pitch 邮件(三变体,投稿窗口:①层发布反响出来后)

**通用骨架**:subject 一句 + 正文 5 句(问题/架构/证据/可复现/链接),120 词内。

**A. TLDR AI(工具/开源条目向)**
> Subject: Open-source local-first agent memory (LongMemEval-S 75.4%, reproducible for $3.50)
>
> Hi TLDR team — quick one for your open-source/tools section. nautilus-compass is a local-first memory layer for AI agents: verbatim writes with zero LLM calls (local BGE-m3), all intelligence in read-path routing. On LongMemEval-S it lifts e2e accuracy 42.6%→75.4% with fully disclosed judge accounting; same-questions-same-criteria vs a mem0 reproduction: retrieval P@1 0.890 vs 0.774. Everything reproduces for ~$3.50 of GPU time — scripts, harness and evidence chain are in the repo. Modified MIT (self-host free forever). https://github.com/chunxiaoxx/nautilus-compass — happy to answer anything.

**B. AlphaSignal(研究+工程向)**
> Subject: We caught our own LLM judge failing 5× — and the memory system it evaluates
>
> Hi — two things your readers might dig. (1) A judging-hygiene postmortem: a gateway outage silently recorded 14.2% of eval questions as wrong answers; we found and fixed five such judge-infrastructure failures, with a preregistration protocol to prevent them. (2) The system it evaluates: local-first agent memory with zero LLM calls on the write path; LongMemEval-S e2e 42.6%→75.4% (dual accounting), head-to-head retrieval vs mem0 0.890 vs 0.774 P@1 on identical questions/criteria. Reproduces for ~$3.50; all scripts open. arXiv paper + repo: https://github.com/chunxiaoxx/nautilus-compass

**C. Interconnects(深度分析向,个人化)**
> Subject: Why write-time compression loses: an agent-memory bet, 500 questions, and five caught judge failures
>
> Hi Nathan — I've spent 130 days building a local-first agent memory layer around one contrarian bet: compression at write time is a blind wager on future queries, so the write path should be verbatim and free (zero LLM calls), with all intelligence at read time. The post has the numbers (LongMemEval-S 42.6%→75.4%, dual accounting; mem0 head-to-head P@1 0.890 vs 0.774 on identical questions) and, I think the more interesting part, the eval-hygiene story: five caught failures in our own LLM judge, incl. one that silently mis-graded 14.2% of questions — plus the preregistration protocol we now run. Repo + scripts: https://github.com/chunxiaoxx/nautilus-compass

## 6. MCP 社区公告(Discord/论坛,~110 词)

> We shipped an MCP server for long-term agent memory — local-first (SQLite + BGE-m3, zero cloud), multi-tenant with scoped tokens, and a read-path router that lifted LongMemEval-S e2e from 42.6% to 75.4%. Write path makes zero LLM calls: verbatim storage, sub-second reads (p95 0.34-0.80s). Hosted open beta at compass.nautilus.social (self-serve signup → scoped token → any MCP client) or self-host with three commands. Everything reproducible (~$3.50), evidence chain in repo. Modified MIT. Would love feedback from folks running multi-agent setups: https://github.com/chunxiaoxx/nautilus-compass

## 7. 待产队列

- ~~中文圈三件(知乎答/公众号技术文/V2EX)~~ ✅ 已产出(见 §1)
- r/MachineLearning 论文贴——paper2 arXiv ID 出来后 24h 内
- Product Hunt 文案——hosted 正式定价时(第④层)
- demo 录屏成片——用户录制后剪 75s 版+GIF
- 中文圈配图(公众号封面/金句卡排版)——排版期做

## 8. 发布记录(执行后回填)

| 日期 | 渠道 | 链接 | 24h 数据 | 备注 |
|---|---|---|---|---|
