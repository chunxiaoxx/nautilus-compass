---
name: orgfuel-ORGH-dd3ccc9c76aaff2a-3e79e48b40
description: "工具决策记录 reddit_watch.py Reddit comment watch — launch-day rea"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-dd3ccc9c76aaff2a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 reddit_watch.py
Reddit comment watch — launch-day read-only monitor (9/8 值守工具).

只读,零凭据:走 Reddit 公开 .json 端点(浏览器等价读取,单帖低频轮询),
不需要 API app(Responsible Builder Policy 对新账号关了 API 申请也没关系)。
不投票、不发帖、不自动回复——写侧永远人工(launch_plan 红线)。

Usage:
  python tools/reddit_watch.py init <post_url_or_id>  # 定帖子+快照已有评论
  python tools/reddit_watch.py check                  # 新评论+未回复列表
  python tools/reddit_watch.py mark <comment_id>      # 标记已回复
  python tools/reddit_watch.py status
