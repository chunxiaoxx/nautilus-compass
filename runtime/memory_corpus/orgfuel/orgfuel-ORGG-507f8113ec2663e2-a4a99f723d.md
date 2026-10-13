---
name: orgfuel-ORGG-507f8113ec2663e2-a4a99f723d
description: "判读档判例 CLOUD_DAEMON_ROOTCURE_PLAN_20260930 · 三 · 根治四刀 v3.2(结构"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-507f8113ec2663e2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 CLOUD_DAEMON_ROOTCURE_PLAN_20260930 · 三 · 根治四刀 v3.2(结构性,非调参)
## 三 · 根治四刀 v3.2(结构性,非调参)

**刀 A(主刀)· 向量 numpy float32 化**
- cache 值 (mtime, vec) → vec=np.float32[1024];旧 pkl 读入时惰性转换(一次性);cosine 改 np.dot(顺带 5-10x 提速)。
- 效果:驻留内存降 8x——10 项目全驻 ~6.4G→**<1.2G**。LRU 基本不再触发,**churn 根因消失**。

**刀 B · 容量预算制替代项目数 LRU**
- 新 env COMPASS_EMBED_BUDGET(默认 300k 向量,≈numpy 化后 ~1.2G 封顶);超预算才逐出最久未用项目;逐出只清 entries,pkl 回读路径保留(不再互搏)。
- 效果:项目数无限增长也有硬顶;预算内零逐出。

**刀 C · listen 前置 + status/ping 豁免上云**
- bind/listen 移到 eager-load 之前:重启立即接客(过载请求排队/快速失败,不再 socket 拒);本地 MSG_PEEK 豁免补丁同步部署。
- 效果:冷启动零断供;status/ping 永远可探。

**刀 D · 孤儿 pkl 盘点清理**
- 10261 个 pkl → 对账活跃 ~75 项目 hash → 孤儿**移档**(移 /tmp/orphan_pkls_20261001/,留 7 天,不直接删)→ 磁盘回收 ~1.4G;warmup glob 从 O(10261) 降 O(80)。
- 删除前列清单人工确认(dangerous-commands 纪律)。
