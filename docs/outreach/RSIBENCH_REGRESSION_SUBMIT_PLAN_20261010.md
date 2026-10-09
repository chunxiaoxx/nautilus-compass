# rsi-bench 25 题回归集投递预案(窗前预检 · R460 · 窗 10/13-15)

> 材料:runtime/outreach/rsi_regression_set_v1.jsonl **26 行定版**[实测核对,与 R355 一致]。
> 投递目标:rsi-bench #4(effective-gain gate 提案 issue)跟评。窗 10/13-15(开业后,R417 口径)。

## 一、投递文案草稿(窗开日直接贴)

---

**Regression set delivery (as proposed in this issue's effective-gain gate discussion)**

Following our Round-1 judging work, we're delivering the promised 25-case regression set — 26 judgment rows across two arms (A/B), each with: `qid`, `arm`, `defects[]`, `patch_found`, `patch_chars`, `expectation`, and a sha-anchored `anchor` to the full artifact.

Purpose per this issue: a **fixed, reusable benchmark for verifier regression** — run your verifier against these cases after any change and compare verdict drift. Every row is recomputable from the anchored artifacts; criteria were preregistered and never loosened.

Format: JSONL (26 lines). Criteria disclosure: nautilus.social/criteria/ · Live leaderboard example: nautilus.social/leaderboard.html · Everything we publish is recomputable for free — if a number doesn't reproduce, the erratum ships same day.

---

## 二、窗开日 checklist(零现场)

1. [ ] 26 行 jsonl 原文贴入跟评(或 gist 链接,二选一——issue 可读性优先贴原文,26 行短);
2. [ ] 文案上方三链接 200 复验(criteria/leaderboard/intake);
3. [ ] 贴后 48h 窗纪律(不重发);回音即升外联台账;
4. [ ] rsi-bench#4 若已关/stale——先 keep-alive comment 再贴(记忆:openclaw 同型先例)。

## 三、预检结论

- 材料 ✅ 26 行完整/字段齐/锚结构合规;
- 窗口径统一:10/13-15(R417 较新口径,排在开业三件之后);
- 无阻塞项;窗开日现场工作=贴评论一条,~10 分钟。

—— compass · rsi-bench 回归集 · R460 · 2026-10-10 晨
