---
name: orgfuel-ORGQ-R147-ab07530466
description: "### R147 · 2026-10-05 0:3x-1:3x(用户拍:归因制式化优先+smoke 空窗即跑+push;"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R147
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R147 · 2026-10-05 0:3x-1:3x(用户拍:归因制式化优先+smoke 空窗即跑+push;smoke 执行轮)
- **push 5 枚**:fb236699..61e8f8d8(R143-R146 全上 origin)
- **归因报告制式 v1 落地**:docs/metering/ATTRIBUTION_REPORT_TEMPLATE_V1_20261005.md(制式八段:识别/摘要/现象/归因链/修复建议≤3/反证自查/消费记录/判绩账;装订线收费物;首件回填=RPT-G1-2407)
- **smoke 执行**(空窗即跑,脚本自带 GPU 守门):PID 2132014 训练 200 步全完,**峰值显存 22.4G(S2 门 36G 大幅 PASS)**;S4 推理阶段;结果 report 下轮收
- **兼容补丁三件套**(14B 环境实测,记入脚本注释):①torch.float8_e8m0fnu 占位(transformers 5.10 模块级引用 torch 2.7 符号,本机 2.6)②transformers 顶层挂回 PreTrainedModel/PretrainedConfig 真身+Bloom 空壳(peft 0.21 顶层 import 病)③venv=壳,实走系统 torch 2.6+transformers 5.10.4
- **迁移坑实测**:lab_tok 丢原版 padding=True(三态词 1/1/4 token 不齐→"excessive nesting"炸)——最小重现 C_FAIL 定位,补齐修复
- **pgrep 自匹配再演**:bash -c 命令串含关键词→ALREADY_RUNNING 误判没启动;改 ^锚定 cmdline 法
- **turbo**:23G/29G 快完

