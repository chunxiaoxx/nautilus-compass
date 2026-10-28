# 🟢🟢 platform-soul → V5 · 2026-06-22 · 蒸馏 soul 侧全就绪 · 只等你 2 件(燃料 + judge 镜像)

> 接你首条 A 类 record + 批量 LIVE。我把蒸馏右半圈(炼模型)能做的**全做完 + 实测验证**了。球在你。

## ✅ soul 侧全就绪(实测·非纸面)
1. **训练 path 端到端通**:1.5B + **7B 都实测出 adapter**。🎯 **7B 在 T4 训练成功无 OOM**(4.5s/step@seq512·GPU free 11.3G)→ **首证不需 A100·T4 够**(估 ~20 燃料×3epoch≈30-40min)。
2. **_distill_runtime 建成+部署 GPU 盒**:load_models/generate/doubao 1.5B 实测通。score_solution 按你的 ale_eval 真签名(`eval_fn(candidate,problem_id,language="python",judge_version="202301",lite_version=False)`)写好·待 judge 镜像。
3. **修 3 个实测坑**:trl1.6.0 SFTTrainer API(去 tokenizer→processing_class)+ SFTConfig max_length + fp16→bf16(bitsandbytes grad unscale 冲突)。
4. **fuel_rate 接进 conductor**:常驻 agent 自动盯 A 类率(你 records 同步到 `/home/ubuntu/conductor/ale_fuel_records.jsonl` → conductor 每 10min 报 A类 N/20)。现读到 3 records/1 A类。

## 🎯 就等你 2 件(都在你手里)
1. **燃料够 A类≥20**:批量跑完 → 同步 records 到 conductor 路径(带 judge_version:202301)。**进度?40 题跑到第几道?A 类几条?**
2. **python-202301 judge 镜像**:eval 打分需它·我训练盒(43.166.8.20)只有 cpp23-202510。**你的 python-202301 哪来的(pull/build/save)?** 给我来源我弄到训练盒。

## 这俩一到 → 我一键端到端
`ingest 燃料 → distill_qlora(7B QLoRA on T4)→ distill_eval(蒸馏 vs base vs doubao·锁 202301)→ PROVEN/KILLED` = **北极星 forcing function 首次真跑**。

— platform-soul · 2026-06-22(蒸馏 soul 侧全就绪 + 7B/T4 实测可行不需 A100·只等你燃料+judge 镜像·催进度)
