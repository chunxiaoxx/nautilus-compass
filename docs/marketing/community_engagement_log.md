# 社区互动台账(dev.to + GitHub · 2026-09-08 起)

> 纪律:真实身份、每 repo/作者每天 ≤1-2 条、技术价值优先、链接只在自然相关时给、
> 不在 bug issue 推销、不复制粘贴同文刷帖(=spam 举报+封号风险)。质量>数量。

## 已发布

| 时间 | 平台 | 位置 | 角度 | 链接 |
|---|---|---|---|---|
| 9/8 深夜 | GitHub | mem0 #7260(rate limit 缺失) | 写侧零 LLM=架构级止血+scoped token+探针开源 | issuecomment-5587908156 |
| 9/8 深夜 | GitHub | MemOS #2345(本地嵌入源) | HF_HUB_OFFLINE 配方+BGE-m3 vs 小模型实测 | issuecomment-5587909009 |
| 9/8 23:3x | dev.to | 4602572(mateo_ruiz 评论) | 两层检测+反问未声明失败模式 | ⏳ 草稿待用户网页贴(API 端点 404) |

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

## GitHub 互动目标池(gh CLI 可直接发,每轮挑 1-2 个)

- mem0/Letta/Zep/MemOS/Cognee 的 **discussions**(评测/选型类,非 bug)——GraphQL 拉取待接
- 新 fresh issue 里 security/scoring 类(有真经验的才评)
- 我方 repo:issue 24h SLA · Reproducibility Wall PR 照登

## 密度目标(用户 9/8 拍板:加大)

- dev.to:发文从周 2-3 提到**隔日更**(素材:判分卫生学/失败实验系列/130 天舰队故事/白皮书拆章);评论每天 3-5 条新鲜相关帖
- GitHub:评论每天 2-3 条目标池;follow-ups(有人回复继续聊)
