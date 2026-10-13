---
name: orgfuel-ORGQ-dfade9184296b7c9-1876ec88f0
description: "轮次记录 R367 · 2026-10-08 深夜二(用户批令执行:A1-A2 清理落地+A4 探针否决+Docker "
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-dfade9184296b7c9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R367 · 2026-10-08 深夜二(用户批令执行:A1-A2 清理落地+A4 探针否决+Docker 悬空 2.3G——磁盘 66→74G)
### R367 · 2026-10-08 深夜二(用户批令执行:A1-A2 清理落地+A4 探针否决+Docker 悬空 2.3G——磁盘 66→74G)
- **用户批"A1-A4+方案一"执行[实测]**:A1 pnpm prune=0 包(无收益);A2 snapd cache 1G 清;**A4 探针否决**(清前活性探针抓到 ecc-shared venv 有两个 uvicorn 在役 8850/8849 自 9/15——列单自身有错,执行前探针制胜);**A3 诊断修正**:containerd 4K 空(k8s 零负载坐实),16G 大头=**Docker 镜像**(8 容器全在跑 Up3w=生产),`docker image prune` 收悬空 2 件 2.3G,`-a` 0B(其余全 active 不可收)。**磁盘 66→74G**;清理后复核:8 容器 Up、espocrm 302、judge-status active。
- **方案一启动**:余 74G 支撑按需镜像分批(S6 30 镜像 4-5 批,峰值 2 个 ~10G 判读跑完即删)——swebench 执行排 10/9-14 窗。
