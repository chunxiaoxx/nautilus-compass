# 社区互动台账(dev.to + GitHub · 2026-09-08 起)

> 纪律:真实身份、每 repo/作者每天 ≤1-2 条、技术价值优先、链接只在自然相关时给、
> 不在 bug issue 推销、不复制粘贴同文刷帖(=spam 举报+封号风险)。质量>数量。

## 已发布

| 时间 | 平台 | 位置 | 角度 | 链接 |
|---|---|---|---|---|
| 9/8 深夜 | GitHub | mem0 #7260(rate limit 缺失) | 写侧零 LLM=架构级止血+scoped token+探针开源 | issuecomment-5587908156 |
| 9/8 深夜 | GitHub | MemOS #2345(本地嵌入源) | HF_HUB_OFFLINE 配方+BGE-m3 vs 小模型实测 | issuecomment-5587909009 |
| 9/8 23:3x | dev.to | 4602572(mateo_ruiz 评论) | 两层检测+反问未声明失败模式 | ⏳ 草稿待用户网页贴(API 端点 404) |
| 9/9 凌晨 | Gmail | **Trajko 回复**(sorovince@gmail.com) | 见 seeds 段 | 1a081c3beb4e3281 |

## Seeds 名单(优先维护:点名致谢/优先回复/进 issues 讨论)

1. **Trajko**(sorovince@gmail.com)——9/4 主动来信,Hivemind 量化平台架构师(4 agent 团队/7471 自检/OOS Sharpe +0.87),Operator Skepticism Protocol 作者,自荐 drift/评测方向合作(附简历)。9/9 已回:数字更新(0.890 vs 0.774 反超)+试用邀请+Reproducibility Wall 首位邀请+合作口径(无席位,开源协作为先)。**跟踪:48h 内若回→深聊;quant 场景是好用例。**

## dev.to 评论草稿队列(用户批量贴,每条 20 秒)

1. **4599143**(Mem0 实操教程 @mukesh_13,9/7):
> Nice walkthrough. One data point for the pruning/extraction tradeoff: we ran extraction-based (mem0 2.0.19) vs no-extraction (verbatim + local embedding, intelligence at read time) head-to-head on LongMemEval-S retrieval, full 500 — extraction lost on retrieval accuracy (0.774 vs 0.890 P@1) and adds a paid LLM call per write. Worth benchmarking pruning aggressiveness against no-prune-verbatim before committing.

2. **4584021**(「Memory is the Part That's Real」 @mukesh_13,9/5):
> Agreed — and the under-discussed half is judging whether memory actually helps. We caught our own AI judge failing silently 5 times during one 500-question eval (14.2% of answers mislabeled). Cross-harness numbers in this space mostly aren't comparable; judge hygiene is the missing foundation.

3. **4579358**(选型指南 @realmrmemory,9/5):
> For the comparison matrix: one school worth adding is no-extraction/local-first — verbatim storage, local embedding, retrieval intelligence at read time (BM25+dense fusion, question-type routing). Cheaper to run (zero LLM at write) and in our head-to-head it beat extraction on retrieval accuracy.

4. **4486125**(ContextForge vs Mem0 vs Zep @alfredoizjr,8/25):
> Useful roundup. If you do a follow-up: same-questions-same-criteria head-to-heads with published scripts are what actually move this space — self-reported numbers from different harnesses aren't comparable. We publish ours (including failed experiments), ~$3.50 to re-run.

5. **4607317**(MCP Memory Server 选型 @mind_anthony,9/8):
> Good overview. One axis often missing from these roundups: write-path cost & privacy — whether the memory layer calls an LLM/cloud on every write, or stays fully local. It changes both the egress profile and running cost dramatically.

6. **4602572**(Procrastinating/意图-行动差距 @IT Path Solutions,9/10 收到·用户转):
> This distinction is the right one — and it's sharper than our post. We framed the intention-action gap as an evaluation problem; you're pointing at the layer below it: progress detection. A rewritten plan is a log event. State changing is an event in the world. Confusing the two is how an agent looks busy forever.

> Two examples from this same project. Our local memory daemon kept passing "is it running?" checks — process alive, port listening — while a stale instance accepted connections and answered nothing. The liveness signal said healthy; the state-based probe (a real round-trip that required a response) said half-dead. And we now preregister pass/fail gates before eval runs — explicit failure conditions, in your state-machine sense — because an agent (or a team) will otherwise negotiate the definition of progress after seeing the result.

> The version we landed on for claims themselves: every "this changed" carries a content hash and a signed receipt, so "state actually moved" is verifiable in bytes rather than narrative. Your framing generalizes that from claims to agent loops. Worth a follow-up post — thanks.
>
> (repo 在回复尾部自然带一次即可:github.com/chunxiaoxx/nautilus-compass)

## GitHub 互动目标池(gh CLI 可直接发,每轮挑 1-2 个)

- mem0/Letta/Zep/MemOS/Cognee 的 **discussions**(评测/选型类,非 bug)——GraphQL 拉取待接
- 新 fresh issue 里 security/scoring 类(有真经验的才评)
- 我方 repo:issue 24h SLA · Reproducibility Wall PR 照登

## 密度目标(用户 9/8 拍板:加大)

- dev.to:发文从周 2-3 提到**隔日更**(素材:判分卫生学/失败实验系列/130 天舰队故事/白皮书拆章);评论每天 3-5 条新鲜相关帖
- GitHub:评论每天 2-3 条目标池;follow-ups(有人回复继续聊)

## 2026-09-10 21:36 (dev.to v3 主帖发布)

- **动作**: 草稿 4621352 翻转发布(PUT 200 → GET 复验 published_at=2026-09-10T13:36:53Z)
- **URL**: https://dev.to/chunxiaoxx/we-beat-mem0-on-longmemeval-s-retrieval-116pt-p1-full-500-with-a-fully-local-memory-layer--2i35
- **title**: We beat mem0 on LongMemEval-S retrieval (+11.6pt P@1, full 500) with a fully local memory layer — no LLM at write time(发布后锁死,勿再动)
- **tags**: ai,llm,opensource,machinelearning · ai_disclosure=fully_autonomous
- **正文要点**: 表格对打 0.890/0.774 · Sealed not claimed 段(verify 命令内联)· 81.6% 不入包坦白 · 94.4% 口径 caveat
- **同日 GitHub 资产配套**: v3.2.0 Release + Profile README + Discussions #56/#57(verify 链接全部可解析——44 commit 已推,不再是死链)
- **值守**: 1-2h 内查 views/评论;评论模板在 launch_plan §6
