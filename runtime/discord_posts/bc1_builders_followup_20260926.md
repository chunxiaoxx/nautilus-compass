[builders-chat follow-up · BC1 首小时零反应触发 · 9/26 20:1x 发]

Quick follow-up from the show-and-tell post — the part builders here might actually use.

We benchmarked mem0 as a memory layer on an audit-style task (18 questions, same LLM, only the memory path different): direct access **16/18** → through default mem0 **11/18** → through mem0 with write-time compression off **18/18**.

The 7-point drop traces to one behavior: mem0's semantic compression turns structured logs into natural-language sentences and drops exactly the machine-checkable fields an audit needs (e.g. a null that means "no receipt exists"). Compression off, originals kept — the fields survive, the score recovers.

If you're building anything audit / compliance / forensics-flavored on top of a memory product: test your write path, not just your retrieval. Full evidence chain (what each arm retrieved, answered, and why it scored) is public: https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/benchmarks/BC1_LAUNCH.md

The benchmark itself is free to sit — 30 items, open scorer, signed three-state report: https://github.com/chunxiaoxx/nautilus-compass/issues/new?template=exam-signup.md
- msgId:1553377947384152195 · 直链:https://discord.com/channels/1483217544214085663/1551020999112261804/1553377947384152195 · 20:09 上墙
- 首小时读数(show-and-tell 主帖):0 reactions / 0 replies,频道活跃但讨论在他人帖 → 触发本 follow-up
- 发出配置:scripts/post_discord.py 回写版首跑 GREEN(ready/focus/1113 字/读回全过)
