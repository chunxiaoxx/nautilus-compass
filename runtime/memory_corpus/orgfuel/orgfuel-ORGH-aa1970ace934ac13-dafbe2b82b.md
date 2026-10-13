---
name: orgfuel-ORGH-aa1970ace934ac13-dafbe2b82b
description: "commit 9b7da6503473 2026-08-22 feat(exp): recall 有用性对照实验 · 首"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-aa1970ace934ac13
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9b7da6503473 2026-08-22
feat(exp): recall 有用性对照实验 · 首次外部证据 delta=1 + 语义 recall 复活
- F2 部落事实 control 0/3 → treatment 3/3(recall 改变任务结局首证);F3 负对照 delta=0 判别力成立
- 检索层 hit@3 = 9/9;F1 机制注入成功但表达式合规败(同 Gate B 方差,分层归因)
- 根因修复:本地语义 recall 曾 100% 坏死(torch Store Python 长路径 WinError 206)
  → torch 装短路径 C:/pylibs + daemon PYTHONPATH 重启,BGE 26s 加载复活
- 产品缺口:recall 不返回正文;坑:网关过滤 urllib UA、429 需退避

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
