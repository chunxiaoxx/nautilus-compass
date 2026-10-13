---
name: orgfuel-ORGQ-fb75ea62e230ab42-5f8dd0e670
description: "轮次记录 R402 · 2026-10-09 晨九(主件轮:Embedder 对拍开跑——判据冻结+A100 通道+语料"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-fb75ea62e230ab42
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R402 · 2026-10-09 晨九(主件轮:Embedder 对拍开跑——判据冻结+A100 通道+语料上岛+双模型下载中)
### R402 · 2026-10-09 晨九(主件轮:Embedder 对拍开跑——判据冻结+A100 通道+语料上岛+双模型下载中)
- **预注册判据冻结**(docs/metering/EMB_BAKEOFF_PREREG_20261009.md):三候选(bge-m3 锚/Qwen3-Emb-0.6B/4B)×三评测集(A 全库自监督 30 查询 seed42/B 中文切片/C 实弹 J4 三查询);**换模型门=Set A R@1≥+2.0pp 且 Set B≥+2.0pp 且 Set C 不降(3/3)**,同分留任;负结果照发。
- **工程就绪[实测]**:paramiko 5.0.0 密码通道(a100_env,凭据不落仓不打印);A100 实探=40G 卡余 39G/transformers 5.16.1/modelscope 1.40.0/embed_server 在役;语料 160 md 上岛解压;eval 脚本上传(三模型官方用法:bge CLS 池化/Qwen3 末token池化+指令前缀,fp16 归一化余弦);**双模型 modelscope 顺序下载中**(0.6B 57%·4B ~8G 殿后)。
- 下载完即跑评测→判读(预注册门)。
