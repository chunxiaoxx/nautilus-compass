---
name: orgfuel-ORGQ-0db8903fffed4d5b-bdb35b964a
description: "轮次记录 R458 · 2026-10-10 晨二(主件轮:7B 下载核查→🔴勘误第 8 例——Qwen3 系无 7B,"
metadata:
  type: reference
  source: org_fuel:queue_r3
  pf_id: ORGQ-0db8903fffed4d5b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R458 · 2026-10-10 晨二(主件轮:7B 下载核查→🔴勘误第 8 例——Qwen3 系无 7B,实为 8B·Qwen3-8B 下载跑起[实测 376M+])
### R458 · 2026-10-10 晨二(主件轮:7B 下载核查→🔴勘误第 8 例——Qwen3 系无 7B,实为 8B·Qwen3-8B 下载跑起[实测 376M+])
- **勘误第 8 例[实测]**:"7B 对拍"口径误——hf-mirror 实测 Qwen/Qwen3-7B=404 而 8B=302 在,**Qwen3 系官方无 7B 尺寸(0.6/1.7/4/8/14/32B)**,实际对象=Qwen3-8B;registry 文案勘误已部署(外网 grep 8B 对拍×2),corpus_stats 字段名 sevenb_* 保留(schema 稳定);预检档补勘误段。
- **下载链排障**:昨晚"7B"下载实为空壳(modelscope record not found=repo 不存在的表象);换 hf-mirror 通道**Qwen3-8B 下载健康跑起**(376M/67% 文件/3 进程,~16GB 预计 1h 内)。完成后 7B(8B) 资源预检四项全绿,对拍就绪状态。
- 附带:信箱 0 新函(10899/10916 已 ack)。
