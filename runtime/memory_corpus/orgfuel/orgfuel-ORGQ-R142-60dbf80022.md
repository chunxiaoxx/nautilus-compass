---
name: orgfuel-ORGQ-R142-60dbf80022
description: "### R142 · 2026-10-04 22:5x-23:1x(用户拍:重下 turbo+基座库存立档) - **T"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R142
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R142 · 2026-10-04 22:5x-23:1x(用户拍:重下 turbo+基座库存立档)
- **Turbo 源定位**:官方 Qwen 组织无此 id(ModelScope API 实查);从 dl log 挖得真实源=`ewinregirgojr/Qwen3.8-14B-Instruct-Turbo`(第三方转载,25 文件)——首次下载源未留档教训入库存档纪律
- **重下启动**:中途抓出双进程竞争(上条超时命令远端已实际启动,重复启动第二个,双亡残留 1.1G);护栏式重启单进程 PID 1994506,断点续传,~3.4h;**完成验证留下轮巡检**(10 分片+index.json 齐,du≈29G)
- **库存档立制**:runtime/model_inventory.md(A100 两 14B+1.7B 动态权重载体+VL-7B 待核;删模纪律=先列用途清单请用户确认+下载源必须留档)+10/4 删模事件记录
- 下轮第一件:**turbo 下载完成验证**;回执群(3090/3074/3065/3066/3053/3054/3037);calib60 待用户交回
