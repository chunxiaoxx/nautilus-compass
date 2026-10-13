---
name: orgfuel-ORGH-86597ad74d49d812-2cdcac1dd2
description: "commit b978227d8ea5 2026-05-13 feat(plugin): v1.7 · 4 信号闸真活 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-86597ad74d49d812
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit b978227d8ea5 2026-05-13
feat(plugin): v1.7 · 4 信号闸真活 · importance gate + numeric_claims + expansion + decay
#1 importance gate · session_*.md 必须 drift=red 才进 recall index
   · feedback_*/reference_*/anchor_* 全保留
   · 真测: 767 → 56 entries (-92.7%)

#2 numeric_claims 反幻觉 hook · 5 patterns (entries/percentage/agents/tools/port)
   · stop_hook 写时 ingest · recall 头部嵌 cross_ref alert
   · jsonl append-only 审计留痕 · 真测 2 alerts 触发

#4 query expansion · 18 keys 同义词追加 · 提升 BGE recall
   · 'daemon 挂了' → 守护进程 BGE 9876 9877 systemd · hit 0.553

#5 archived_at decay · 30d+ session drop · query 含历史词 bypass

#3 (loop_anchor 漂移闸) 砍 · plugin 无 hook 点访问 /loop iteration
