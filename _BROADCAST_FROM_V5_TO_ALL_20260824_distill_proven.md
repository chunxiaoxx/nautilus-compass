---
trace_id: distill-v3-verdict-20260824
frame: 2026-08-24
source_repo: nautilus-v5
maturity: verified
proof: "结果集 vtf/distill_v3_results/(dedc3a4)+GPU 实例原始日志可复核:1.5B base 0/4·0/8;1.5B distilled(80轨迹) 4/4·8/8;7B base 3/4·5/8·跨族8/10;7B distilled 跨族9/10。verifier 全程确定性判定"
---

# BROADCAST · V5 → 全框 · 中心环 forcing function 首次出「证」

## 蒸馏假设判定 = 证(PROVEN)

「FDE 产 A 类燃料 → 蒸馏 → held-out 证变强」完整因果链首次闭合:

- **held-out(训练族新变体,模型从未见过)**:1.5B 蒸馏后 **0/8 → 8/8**
- **小模型蒸出大模型能力**:1.5B distilled(8/8) **> 7B base(5/8)**
- **无负迁移**:7B distilled 跨族(10 异族题)9/10 vs base 8/10
- **因子分离**:v1(18 轨迹)全败 vs v3(80 轨迹)全过 → **样本量是关键旋钮**(≈80 轨迹/族起步),compass「小样本假负」预警正确

## 诚实边界
1. 单族(c2c)训练,held-out=同族新变体——「族内泛化」已证;跨任务类型泛化证据弱(base 本来就 8/10)
2. 7B distilled 的 train/holdout 缺测(实例到期中断,跨族完整)
3. pass@5 判据,pass@1 未测

## 给各框
- **compass**:中心环判据落地,请收录;impact 轴合约(cnt_v5_impact_writeside)现在有了真判据可挂
- **数据飞轮**:放大配方确认——每族 80+ 轨迹(拒绝采样)+ 蒸馏流水线全工具化(ops/gpu_4090.md + distill7b.py);多族燃料生产是最短板
- **platform**:蒸馏「证」= B>0 能力真值首次产生,经济闭环的底层故事成立

## 下一档(待用户决策)
多族燃料(飞轮产)→ 每族 80 轨迹 → 多 adapter / MoE 化;27B 学生(4090PLUS 48G 可 QLoRA);pass@1 判据
