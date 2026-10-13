---
name: orgfuel-ORGG-6c6a91a99c1f8ca4-99e7a2fccc
description: "判读档判例 DEADLINE_RUNBOOK_20261009 · 01 · S6 垫跑(夜班已实质起跑) ## 01 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6c6a91a99c1f8ca4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 DEADLINE_RUNBOOK_20261009 · 01 · S6 垫跑(夜班已实质起跑)
## 01 · S6 垫跑(夜班已实质起跑)

- **现状[实测]**:pull_batches 后台跑,#17/30 进行中,#1-16 OK(单镜像均值 ~1.9G);余 37G;护栏=余量<25G 自停(预计自然停在 ~#23)。
- **晨检**:`tail -20 /home/ubuntu/s6_rerun/pull_batches.log`+`docker images | grep -c sweb.eval`+`df -h /`——报三数(完成数/余量/是否触 GUARD)。
- **扩容切换**(候用户 a/b 拍板):
  - a) 用户控制台扩 180→280G → 平台 growpart+resize2fs+df 三验 → **我方重跑 `nohup bash /home/ubuntu/s6_rerun/pull_batches.sh`(EXISTS 自动跳过,只拉剩余)**;
  - b) 用户供国际站 SecretId/Key → 平台 tccli intl 代执行 → 同上;
  - 判据不变:30/30 镜像齐→swebench run→判读岗 L2 深度(执行者 v5/平台协同,排期 10/9-11)。
