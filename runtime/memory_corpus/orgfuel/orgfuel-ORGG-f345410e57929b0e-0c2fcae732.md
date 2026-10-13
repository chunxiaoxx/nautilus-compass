---
name: orgfuel-ORGG-f345410e57929b0e-0c2fcae732
description: "判读档判例 JUDGE_RETRAIN_RUNBOOK_20261001 · 六 · 命令速查(全流程 <1h) ## "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f345410e57929b0e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_RETRAIN_RUNBOOK_20261001 · 六 · 命令速查(全流程 <1h)
## 六 · 命令速查(全流程 <1h)

```bash
# 1) 上传新三折(本地切好后)
python -c "import paramiko; ..."  # sftp.put → /root/runtime/verdict_corpus/
# 2) 训练(setsid 后台,日志 /root/runtime/judge_lora/run.log)
(setsid bash -c 'python3 /root/tools/train_judge_lora.py && echo DONE' > .../run.log 2>&1 &)
# 3) 监控(p2v2_monitor.py 改 LOG 路径即可)
# 4) 拉回(p2v2_pullback.py)+ 判据判定 + 通报函
```
