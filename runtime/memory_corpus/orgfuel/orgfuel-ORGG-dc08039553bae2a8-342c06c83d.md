---
name: orgfuel-ORGG-dc08039553bae2a8-342c06c83d
description: "判读档判例 DOGFOOD_EFFECTIVENESS_20261006 · 二、灯下黑(抓到并已修) ## 二、灯下黑"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-dc08039553bae2a8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 DOGFOOD_EFFECTIVENESS_20261006 · 二、灯下黑(抓到并已修)
## 二、灯下黑(抓到并已修)

**云端 compass daemon 生产瘫痪 19h 无人察觉**:
- [实测] daemon.log 30.3 万行中 **19.5 万行(64%)=overload 拒连**,自 10/5 20:14 持续——五框接云 MCP 的统筹基建实质失效;
- 根因链:云端 projects 数(356)> COMPASS_ENTRIES_CACHE_MAX_PROJ(256)→ 每次 recall 触发 LRU trim 逐出+重 embed(churn 复活,v3.1 根因换形)→ CPU 106% 空转+查询慢 → inflight 32 满 → 拒连;
- **为何没人发现**:本地 hook 走本机 daemon(9876 正常),业务侧判分走信箱/A100 通道——**云端通道无任何消费者告警,probe.py 五源也不含它**(监控盲区);
- 修复 [实测]:drop-in `COMPASS_ENTRIES_CACHE_MAX_PROJ=500`+restart → overload 零新增/evict 尾流/CPU 106→60-82%(服务负载);**零改码**(env 运维);
- 防再犯:probe.py **第六源上线**(cloud-daemon 过载计数,基线 195013,新增 >50 即 🔴)。
