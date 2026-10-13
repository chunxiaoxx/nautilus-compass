---
name: orgfuel-ORGM-8aeab17bb330bbfe-7c73d943a5
description: "记忆条目 m5-memgate-deploy-lessons-20261009.md # M5 部署四课(10/9 凌晨"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-8aeab17bb330bbfe
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 m5-memgate-deploy-lessons-20261009.md
# M5 部署四课(10/9 凌晨 · 主件制 R369)

1. **cherry-pick 路线 ✓**:成品分支隔 24 天后合入最新 main 零冲突(1121328+de0552b 直接 pick);merge-ready-0915 经 GitHub 中转分支(memgate push→主仓 fetch)跨 clone 传递对象,本地 fetch 超时走此路。
2. **🔴双进程同端口事故**:nohup 起 9878 测试实例时旧实例 kill 未生效(MSYS kill 对 Windows PID 无效),两个进程同时 LISTENING 同端口(8/30 双进程写文件事故同型)——`netstat -ano | grep :PORT` 拿 Windows PID→`taskkill //PID x //F` 精确清杀;nohup 后台进程必须用 netstat/taskkill 验杀,不能信 MSYS kill 静默。
3. **EMBED_BUDGET 渐进消化(v3.0.9)对 dedup 的语义影响**:冷文件 embedding=None→dedup_check 对旧记忆漏检(fail-open 静默),155 条仅 ~24-48 条有向量;修法=coverage 字段披露(daemon.py v2.5.1)而非改渐进机制;冒烟判据须用 24h 内热记忆。重启后索引"渐进变冷"——**重启即 RED 假警报**(J4 gate 老文件跌出 hit@3=无向量不可打分,非代码回归),暖机后自愈;Docker 悬空镜像层(2.3GB)误记为 containerd 是另一例误诊。
4. **fast path 环境差虚警**:测试进程装了 inotify_simple→_
