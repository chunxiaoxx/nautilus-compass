# 你的 10 分钟操作手册(9/10 · ①HN+③Reddit+②表单即贴)

> 分工:①③你发(账号在你手里),②④我做(Smithery 配置已验合规+Trajko 草稿已备)。
> 每步都给精确文案,照抄即可。

## ① Hacker News(5 分钟,窗口:今晚北京 21:00-24:00 = 美东上午)

1. 打开 https://news.ycombinator.com/submit(登录 chunxiaoxx)
2. title 贴(⚠️ HN 标题提交后不可改):
   ```
   Nautilus-compass: Local-first agent memory – write path makes zero LLM calls
   ```
3. URL 填:`https://github.com/chunxiaoxx/nautilus-compass`
4. 提交后**立即发首评**(text)——第一句必须亮身份(防 flag):
   > One of the authors here (solo dev — 130 days, 771 commits, most of them by my own agent fleet, which is itself the best demo). The unusual part: every number in the README ships as a sealed pack — sha256 manifest, claims recomputable from bytes, ed25519-signed receipt. Verify without trusting us:
   >
   >     git clone https://github.com/chunxiaoxx/nautilus-compass && cd nautilus-compass
   >     python -m tools.verifypack verify runtime/verifypack/arma_summary/pack
   >
   > → 8/8 claims recompute from bytes (0.754 all-judged / 0.700 conservative on LongMemEval-S full 500). One figure we deliberately did NOT seal: the 81.6% dual-accounting number — it can't recompute from pack-internal bytes, and unverifiable numbers don't get sealed. Full protocol: docs/REPRODUCIBILITY_WALL.md. Ask me anything about the read-side routing or the failure experiments.
5. 提交后回来说一声,我盯评论(24h 内回复是 HN 礼仪,我来起草你贴)

## ③ Reddit 小 sub 矩阵(每 sub 3 分钟,今天任意时间)

⚠️ 发前 30 秒读一下该 sub sidebar 的自我推广规则;一天最多发 2 个 sub,别同文轰炸。

**r/LLMDevs**(最对口):

> **Title:** I benchmarked mem0 vs my local-first memory layer on LongMemEval-S (full 500) — head-to-head, evidence in repo
>
> We ran mem0 2.0.19 (latest PyPI) against our open-source memory layer on identical questions + judge criteria: P@1 0.890 vs 0.774, P@5 0.978 vs 0.916, MRR 0.929 vs 0.834. Away game too: LOCOMO n=1986, 0.644 vs 0.592.
>
> Design bet: zero LLM calls at write time (verbatim + local BGE-m3, all intelligence at read time). Full e2e (42.6%→75.4%) with preregistered gates, failure experiments included. Every number ships as a sealed pack you can recompute in two commands — Reproducibility Wall in the repo, contradicting results welcome.
>
> Repo + evidence: https://github.com/chunxiaoxx/nautilus-compass

**r/AI_Agents**:同文,标题改「Show r/AI_Agents: agent memory layer — zero LLM calls at write time, sealed & verifiable benchmarks」。

**r/LocalLLM**(备选,第三天再发):标题改强调 local:`Fully local agent memory (no cloud, no LLM at write): beat mem0 on LongMemEval-S retrieval`。

## ② MCP 表单即贴块(mcp.so / PulseMCP / Glama · 每 site 2 分钟)

三站都用这包(逐字段已在 `docs/marketing/mcp_directory_submissions.md`):

- Name: `nautilus-compass`
- Tagline: `Local-first memory layer for AI agents — zero LLM calls at write time`
- URL: `https://github.com/chunxiaoxx/nautilus-compass`
- Hosted endpoint: `https://compass.nautilus.social/mcp/`(signup: https://compass.nautilus.social/signup)
- Transport: `streamable-http`(hosted)/ `stdio`(local)
- Auth: `Bearer token (self-serve signup)`
- Tags: `agent-memory, long-term-memory, mcp, retrieval, local-first`

**Smithery**(要账号 token,你登录 smithery.ai 后跑):
```
npx @smithery/cli publish
```
(配置文件 smithery.yaml 已在 repo 根,合规;token 在它网页给)

**Anthropic MCP Discord #showcase**(一条,贴完即走):
> nautilus-compass — local-first agent memory, zero LLM calls at write time. Head-to-head vs mem0 on LongMemEval-S full 500: P@1 0.890 vs 0.774, ~$3.50 to reproduce. Sealed & signed benchmarks (VerifyPack). Hosted open beta + local daemon. github.com/chunxiaoxx/nautilus-compass

## ④ Trajko 邀请(我做,等你一句话)

草稿:`docs/marketing/trajko_verify_invite_20260910.md`——你回「发」我就经 Gmail API 发出。

## 节奏总表

| 时间 | 动作 | 谁 |
|---|---|---|
| 现在 | HN 提交+首评 | 你(5min) |
| 现在 | r/LLMDevs 发 | 你(3min) |
| 明天 | r/AI_Agents 发 | 你(3min) |
| 任意 | MCP 三表单+Discord | 你(10min) |
| 任意 | Trajko 邀请 | 我(你点头) |
| 21:03/21:07 | dev.to 两篇自动发 | 已排 |
