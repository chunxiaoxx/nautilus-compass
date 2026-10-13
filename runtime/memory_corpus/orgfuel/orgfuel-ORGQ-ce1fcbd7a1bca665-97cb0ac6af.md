---
name: orgfuel-ORGQ-ce1fcbd7a1bca665-97cb0ac6af
description: "轮次记录 R487 · 2026-10-10 晨廿九(主件轮:8B bf16 训练 smoke 跑通✅[实测 26.4G"
metadata:
  type: reference
  source: org_fuel:queue_r3
  pf_id: ORGQ-ce1fcbd7a1bca665
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R487 · 2026-10-10 晨廿九(主件轮:8B bf16 训练 smoke 跑通✅[实测 26.4G 无 OOM]——配置档证据层 [推断]→[实测] 兑现)
### R487 · 2026-10-10 晨廿九(主件轮:8B bf16 训练 smoke 跑通✅[实测 26.4G 无 OOM]——配置档证据层 [推断]→[实测] 兑现)
- **主件=8B smoke 先行**(EIGHTB_COMPARE_TRAIN_CONFIG 证据层 upgrade_path 兑现,不等语料 3000):8B 版脚本(25 步短训副本)投 A100 实跑——**LoRA 正确挂载(trainable 15.3M/0.19%)+bf16 显存 26.4G 无 OOM[实测]**——配置档"8B bf16 显存可行性=[推断]"升级 **[实测]**。
- **两坑修**:①启动门 2G 拦截(A100 常驻服务 7G=判分+嵌入+rerank)——门阈值参数化 COMPASS_GPU_BUSY_G=12G(真大训练仍拦,常驻共存放行,env 可调);②语料后缀不匹配(脚本要 split_train.jsonl 无 _v1)——软链修正。
- **附带·10941 ack**:platform P0 闭环对表(8001 iptables 封死+v5 bearer 门 401 验证+19 条加固候评估)——turf 边界确认。
- smoke 训练+评测段后台运行中(约 15-30 分钟),终态读数候下轮收割。
