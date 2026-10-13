---
name: orgfuel-ORGQ-R312-05ebed5c7a
description: "### R312 · 2026-10-07 深夜(🔴安全事件:PUBLIC 仓凭据泄漏——当前树已脱敏,历史清除待批) "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R312
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R312 · 2026-10-07 深夜(🔴安全事件:PUBLIC 仓凭据泄漏——当前树已脱敏,历史清除待批)
- **实锤[实测]**:origin/main(PUBLIC)含 **A100 root 密码 40 文件**(自 919d06a9 10/1,暴露 ~6 天);js2 密码 7 文件(实例 10/2 已释放=死密);HF/GH/sk token 零命中(gho_ 为查询文本误报)。
- **已处置**:①当前树全脱敏(43 文件→A100_PW_ENV 占位,commit 62db81cb)②真凭据移 ~/.claude/.cache/a100_env(0600,脚本改 source)③queue.md 本身干净(密码从未入流水)。
- **待用户批(二选一或都做)**:A=轮换 A100 密码(控制台 2 分钟,即刻无害化);B=git filter-repo 历史替换+force-push(除根;hash 全变,cloud 副本重克隆;违反默认不 force 纪律故请示)。
- **README 更新已备未推**(公共仓新章:判读侧成果/NACRE/caliber-bench/部署纪律+repo 描述/topics 已更)——push 被本事件阻塞(58 commit 含密),B 批后一并推。
