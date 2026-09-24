# C1 触达草稿 · T5 jev-compaction(Discord 回帖 · v2 人味话术 · 第 2 试)

> 目标帖:David 2026-09-24 15:50 show-and-tell「jev-compaction: Jev as the
> memory manager for coding agents」
> 直链:https://discord.com/channels/1483217544214085663/1483217545040232493/1552587963529961533
> 仓:https://github.com/Waxmell114514/jev-compaction
> 状态:9/24 起草存档,观察窗后随 D3 批次(9/26)发;发出时复制正文回帖。
> 话术纪律(v2,承 T4 首试):短、无粗体、无推销腔、先给技术价值再给 offer、零价格。

---

Clean design — scoring without rewriting, so recall stays byte-exact, is the right call. The role-gating number (11 vs 21 hidden-code events) is the one that convinced me this does real work.

One thing worth checking on your sidecar: we just calibrated another Jev pipeline (jev-curate, dataset sifting) and caught that score-type questions with a dict `criteria` field 422 on the live API — their tests were all wiremock'd, so it only surfaced against real calls. If jev-compaction uses score questions anywhere, it's a 5-minute check.

The numbers with silent-failure risk here are 0 FP in 2499 and 17/18 injections — if a Jev version bump shifts them, the gate keeps running and nothing tells you. We run independent calibrations (same inputs, blind re-labeling, signed per-row artifacts, accuracy/Brier/ECE at your thresholds) and would run your admission set as a free mini if you want a third-party read. No strings attached.

---

## 发帖操作备忘(发出会话用)

1. nav 直链(上方)→ sleep 4
2. 回帖方式:hover 原帖 → 回复按钮;或直接在频道输入框带引用。CDP 聚焦输入框:
   `document.querySelector("[class*=slateTextArea]").focus()` 后
   Input.insertText(dispatchKeyEvent 合成文本不可靠,用 DOM
   `navigator.clipboard` 或逐段 execCommand insertText——**发帖后立即
   `python scripts/cdp_tool.py lastid` 存回帖直链**)
3. 发出后:本文档头部状态改「已发+日期」;T 表 T5 状态更新

## 复述准确性核对(9/24 对照原帖)

- "scoring without rewriting / byte-exact recall":原帖 "scores text but
  never writes it…comes back byte for byte" ✓
- "role-gating 11 vs 21":原帖 "gating on role halved…(11 vs 21)" ✓
- "0 FP in 2499 / 17/18 injections":原帖 "17/18 planted injections caught,
  0 false positives in 2,499 real segments" ✓
- 422 格式坑:我方 9/24 实测(jev-curate #3,判据档 PROTOCOL 修正记录)✓
