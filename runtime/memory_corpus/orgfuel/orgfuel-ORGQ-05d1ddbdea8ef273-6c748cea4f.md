---
name: orgfuel-ORGQ-05d1ddbdea8ef273-6c748cea4f
description: "轮次记录 R380 · 2026-10-09 凌晨四(死线带:S6 复算实质开跑✅——batch1 端到端完成+磁盘终局"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-05d1ddbdea8ef273
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R380 · 2026-10-09 凌晨四(死线带:S6 复算实质开跑✅——batch1 端到端完成+磁盘终局令执行)
### R380 · 2026-10-09 凌晨四(死线带:S6 复算实质开跑✅——batch1 端到端完成+磁盘终局令执行)
- **10730 磁盘终局令执行✅**:用户裁=用既存数据盘(不购盘/不扩容);①S6 工作目录迁 /data/s6_rerun(preds/清单/脚本全量,fstab 已持久);②镜像策略切"分批用完即删"——超持 19 个 rmi 释放(系统盘 23G→66G),保留首批 2 个;③/data/home-ubuntu 31G 不碰;④data-root 不动(同意);⑤排班表 v1 验收过收讫,10541 闭环;磁盘决策件 #10704 关案。
- **batch1 端到端完成✅[实测]**:分批执行器 batch_run.sh(拉→跑→删闭环,每批2实例)部署 /data;batch1(astropy-14365+django-12304)实跑完成,报告落 /data/s6_rerun/runs(l3r1a…s6_batch_1.json)=**2 实例:0 resolved/1 unresolved/1 error**——管线验证达成;django-12304 复算 error 与回归集原判(格式域 apply fail)方向一致✓;astropy-14365 原跑各分桶无 resolved 记录,复算 unresolved 不矛盾(精确对照留正式判读全量 30 例)。
- 输入源核验:cloud preds_arm_a.json=本地正本 _r181_board30/preds_arm_a.json 逐 id 吻合(无错源,虚警排除);round1_merged 四桶为计数不含 id(查证过程)。
- 剩余 
