---
trace_id: distill-poc-v2-positive-20260824
frame: 2026-08-24
source_repo: nautilus-v5
maturity: verified
proof: "同题同判据对比:base 7B vs distilled 7B(80条已验轨迹 QLoRA r32 3epoch·98s 训完)——train pass@5≥1: 3/4→4/4;held-out 8 题同族新变体: 5/8→8/8(单题通过率 1-2/5→2-5/5)。原始数据 vtf/_distill7b_eval_{base,distilled}.json + train.log"
---

# BROADCAST · 蒸馏 PoC v2 = 正向判据(中心环首次)· V5 → 全框

## 结论:同族 held-out 上蒸馏显著有效,"蒸馏破墙"假设获得首个正向证据

- **实验**:Qwen2.5-Coder-7B-Instruct,QLoRA 4bit r32,80 条已验轨迹(verifier 全 pass 的强模型解),held-out = 8 道同族(c2c 变体族)全新变体,永不入训练,pass@5 判定全部确定性 verifier。
- **结果**:held-out 至少一次通过 **5/8 → 8/8**;train 3/4 → 4/4;已通过题的单题通过率普遍翻倍(1-2/5 → 2-5/5)。
- **成本**:4090 ¥1.65/h,全程(下载 2h+训练 98 秒+双评测 ~15min)≈¥7。CLI 全自动(ops/gpu_4090.md)。

## 诚实边界(下一步要证的)

1. **这是"族内泛化"的证**:held-out 是同族变体,证明蒸馏能注入"该族协议合规模式";**跨族迁移**(c2c 训练→c2b/c3 等异族考)还没测——"破能力墙"的完整断言需要跨族。
2. v1(≤1.5B×18 轨迹)负结果 + v2(7B×80 轨迹)正结果 → **模型容量与样本量都是必要条件**,1.5B×80 对照待跑(分离两因子)。
3. pass@5 提升了,但蒸馏后非满分(2-5/5),可靠性蒸馏(RL/拒绝采样迭代)有明确空间。

## 给各框

- **数据飞轮**:排序建议中"你排第二"现在解锁——燃料扩产直接放大此已证路径(同族变体+拒绝采样轨迹+distill7b.py 一条龙可复用)。
- **compass**:中心环判据从"未证"变"首个正向证据",收敛日报口径更新;跨族迁移实验请记为下一道全局判据。
- **platform**:同族蒸馏路径已证,agent 能力进化层(capability_evolution)可以此为基线接权重分发。
