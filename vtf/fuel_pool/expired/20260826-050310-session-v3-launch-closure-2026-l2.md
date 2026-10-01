---
status: pending_qc
source_session: session_v3_launch_closure_20260824.md
source_project: C--Users-chunx-Projects-nautilus-compass
extracted_at: 20260826-050310
content_hash: sha256:4c0705a4c9a48e34
qc_protocol: control-first-fail (Gate B)
---

- **B 命中计数**:HUD `🧠今日Nhit/1h M`(verification_log 实算)——首日读数 97hit/天,价值首次可见
- **A session 战报**:stop_hook 写 `~/.claude/.cache/compass-last-session.txt`
- **D 池瘦身**:lifecycle 默认 ON(`00e0603`),仅影响带 forget_at 条目(compass 项目 50 条中 1 条,零误伤面)
- **C 中途补召回**:`mid_session_hook.py` v0.7 早已写好但**从未接线**(同 HUD poller 病:建好即死)。已接 PostToolUse(matcher *,每 30 调用+>20min 静默刷新),烟测 exit=0。**教训入册:本仓"未接线的好代码"已两例(HUD poller、mid_session),部署检查项=不止写代码,还要核 settings.json 接线**
