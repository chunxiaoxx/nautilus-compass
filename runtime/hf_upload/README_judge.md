---
license: apache-2.0
base_model: Qwen/Qwen3-1.7B
tags: [judge, verification, NACRE, lora]
---
# NACRE Judge Instance v1 (nacre-judge-v1)

Nautilus 独立判读侧现役判分器(LoRA on Qwen3-1.7B)。

- 三态判读 pass / fail / insufficient_evidence,J1 binary acc **88.51%**(生产评测,ECE 0.072)
- adapter sha16: dbcbab6fd1ff5821 · 判据:预注册(P2_JUDGE_TRAINING_PREREG)
- 部署纪律(PRECOR B/C 实测 291 题,2026-10-07):**只允许 bf16/fp16**——fp16 对 bf16 判定一致率 1.0000,int8 0.9828 FAIL,int4 0.9416 FAIL(禁用)
- 判定表:docs/metering/PRECOR_BC_VERDICT_20261007.md(nautilus-compass 主仓)
- 归属:NACRE 机制·判读实例 v1(机制名+实例版本号,组织对齐账 2026-10-06)
