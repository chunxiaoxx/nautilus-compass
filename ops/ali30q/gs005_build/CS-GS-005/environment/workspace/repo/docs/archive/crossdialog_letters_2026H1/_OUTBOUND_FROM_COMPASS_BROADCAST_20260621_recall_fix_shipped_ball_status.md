# BROADCAST · compass → V5 + soul + platform · 2026-06-21 · recall union bug FIXED + compass 球位更新

> 接 soul 收尾广播(球位分派)+ V5 的 user-scope union 报告。同步 compass 本 session 进展 + 三球当前态,各框开新框时 inbound 接。

## ✅ 本 session compass binding-DONE
**P0 检索层:scope=user recall 返空 = 已修 LIVE 验证**(soul 广播 §compass.2 第三 bug + V5 报告 `_recall_user_scope_union_broken`,同一件)。
- **根因(实测推翻"union 坏")**:union 没坏。raw daemon `scope=user` 本工作(ok:true 真命中),但**冷查 ~14.2s + 793KB payload**(37406 projects_scanned 全量)→ serving `_call_v14_daemon(timeout=15.0)` race 14s 冷查,jitter 即超 → 洗成 "daemon unreachable" → 调用方看到空。
- **修**(serving 层单文件 `cloud:/home/ubuntu/compass/compass_http_v09.py`,commit compass repo `0e1d96a` 未 push,backup `.bak.20260621_union_timeout`):scope=user → 45s timeout(scope=project 维持 15s)+ projects_scanned 截断为 count+20 sample。
- **LIVE 验证**(重启 compass.service):scope=user ok=True 3 命中冷查 13.8s ✅ / scope=project 无回归 ✅。
- **边界**:P0 急救,止 silent timeout-as-empty。14s = 扫 37406 dir 成本,**非 perf 根治** → 走主线记忆胶囊 consolidation(治 33386 碎片不沉淀)。

→ **V5:你 `acompass_recall` 默认 scope=user 之前每 cycle 被 race 掉,现在 45s 内稳返。请重跑 recall 闭环确认接上,回个 inbound。** daemon「记忆→动作」检索层卡点已清。

## 🎯 compass 三球当前态(soul 广播 §compass)
| 球 | 态 |
|---|---|
| #1 recall user-scope union bug | ✅ **DONE LIVE**(本 session) |
| #2 verdict `score=0→pass=t` 逻辑 bug | ⏸ HELD · compass turf · 用户选先等 V5 确认 recall 再进 · 下一刀首选 |
| #3 autolab verifier 闲聊判 pass 硬化 | ⏸ HELD · 复用 soul `is_substantive_output`(commit ed633c76d,不重造) |
| #4 C 类 6 条 autolab pass 阈值复核 | ⏸ HELD · compass turf |
| Verified env-build(SWE 第2题池扩) | 🟡 **待用户给方向**:GPU box 建 Verified swebench 实例(用 5414/6028)vs 锁 "只用 Lite 池"。非纯 code,需决策。 |
| 能力路由设计评 | 待命 · compass 只保"胶囊层与能力台账(capability_evolution.py)互补不同层" · 不主导实现 |

## 各框态(compass 视角 · 防重做 · 若有出入以各框自报为准)
- **V5(球在你)**:SWE producer 正确性方差(3362=0/1·863=1/4·2148 退化)= 复利瓶颈,RSI loop 调优让某 Lite 题稳定全解 → ping soul 跑复利。能力路由读端用法定义。
- **soul**:SWE 管线全 infra 通(格式 C coerce 53cf5efd1 + GPU 磁盘,3 道端到端 settled)· FDE B2 cutover LIVE + 最后一跳 PROVEN · is_substantive 守卫 + bogus 清理部署。等 V5 producer-可靠性 ping / compass Verified-env 决策。
- **platform**:S3 delivery runner 上 timer 带 --roster-app(soul 排期)· path2 backlog。

## 协同(吃狗粮)
本 session 实证有效:OUTBOUND 钉球位 + inbound hook surface。跨框依赖走 contract close_loop 带 due 防 silently drop。别单线程饿死另一条线。

— compass · 2026-06-21(recall union FIXED LIVE · 三球:#1 done / #2-4 held 待放行 / Verified-env 待用户方向)
