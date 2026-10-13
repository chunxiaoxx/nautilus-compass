---
name: orgfuel-ORGM-99fb1828090072ee-fc6f4198dc
description: "记忆条目 cloud-recall-livelock-fillbudget-20261012.md 2026-10-12"
metadata:
  type: reference
  source: org_fuel:memory_r3
  pf_id: ORGM-99fb1828090072ee
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 cloud-recall-livelock-fillbudget-20261012.md
2026-10-12 云端 MCP(https://compass.nautilus.social/mcp/)语义 recall 全拒 13.2h(10/11 23:05→10/12 12:19,1809 次瞬时拒"daemon overloaded - retry")。根因:daemon_v33.py `get_memory_entries` 的 cache fill 无时间预算,单项目冷 fill(千条×嵌入+每50条全量pkl flush,池pkl共1040MB)霸 `_mem_lock` 分钟级;重试风暴填满 32 槽(=线程池×4 的深队列设计);槽是全局资源→一个项目的慢 fill 杀死所有项目的 recall。**embed 代理(A100隧道 19987→8400)全程健康零失败——不是代理的锅**;代理调用有 timeout=8,单次调用挂不了 13h。

根修 v3.3.6:fill 循环加 `COMPASS_FILL_BUDGET_S`(默认30s)预算,超时 break 出部分结果(缺 embedding 条目在下游 `e.get("embedding")`→None 自动跳过,与既有 except 路径同构,部分结果语义安全)。补丁在云端 /home/ubuntu/nautilus-compass/daemon_v33.py(不在 git 仓,生产ops件),备份 .bak-fillbudget-20261012。重启即恢复(pkl 热缓存秒级)。

**Why:** 槽位全局共享+fill 无预算+livelock 三者叠加,任何"别人变慢"都会全局扩散;这是云 daemon 第三次同类事故([[cloud-daemon-storm-rootfix
