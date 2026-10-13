---
name: orgfuel-ORGQ-7811f2c15aab496a-78361a409e
description: "轮次记录 R466 · 2026-10-10 晨十(主件轮:8B 下载守护部署✅——hf-mirror 两断的自动化兜底"
metadata:
  type: reference
  source: org_fuel:queue_r3
  pf_id: ORGQ-7811f2c15aab496a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R466 · 2026-10-10 晨十(主件轮:8B 下载守护部署✅——hf-mirror 两断的自动化兜底,完成自停)
### R466 · 2026-10-10 晨十(主件轮:8B 下载守护部署✅——hf-mirror 两断的自动化兜底,完成自停)
- **主件=下载守护**(tools/qwen8b_dl_guard.sh→A100):loop 120s 检查——断则自动续传(hf-cli 断点续传)/完成判定(4 分片+config+无 incomplete)自停;**部署拉起验证[实测](守护+下载进程在位,15G 推进)**——免手动每轮盯。
- 附带:演练单(8b97795a)候判读岗排期出卡(is_smoke 低优先,如实转排期);8.9→15G 续传轨迹留档。
