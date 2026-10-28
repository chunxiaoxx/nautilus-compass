# FRESH SESSION 接力 · 2026-06-26 · 蒸馏 3B 闭环后 · 料优先

> 上个 session(6/25-26 跨天·极长)收尾接力。先读本文件 + memory `session_20260625_verdict_gate_wired_distill_3way_killed` + `feedback_why_we_repeat_same_walls_four_roots`。

## 一句话状态
蒸馏中心环这一步**没证成**(1.5B/3B held-out 都弱)·但今天收获是**机制 + 认知**,且**全部无悬空**(协调债已还、磁盘已清、方向已派)。

## 关键认知(决定下一步优先级·别走回头路)
1. **1.5B 的 valid 0.0833 是 over-fit 产物**(train_loss→0.0003 背训练集相似解·held-out 偶尔蒙中)·**非真泛化**。
2. **3B valid 0.0 = under-trained 核实**(train_loss 只到 0.22·1.5B 是 0.0003)·**不是"模型大小没用"**(verdict-gate 第3次挡住会错的结论)。
3. 🔑 **真瓶颈是小样本 n=12**(料少·四根诊断根2)·**模型大小换不掉**。→ 重跑 3B more epochs 价值有限(over-fit 更多≠真泛化)。
4. **优先级判明**:**补料 / 换同质料 SWE(结构相似·少样本可迁移) > 重跑 3B more epochs / 租 H800**。

## RESUME 触发点(按这个接)
- **主线 = 等 V5 的 SWE 同质料结果**(我 6/25 已派:修 sklearn `applied=False` spec + 提 strong 解对率·目标 ≥1 道 resolved=True A 类)。V5 产出 A 类 → soul verify(`verify_pathA_one.py`·`/mnt/datadisk0/swe-rsi/venv/bin/python`)→ 喂**同质料 LOO** 对比 ALE·看同质料是否真泛化(对比 ALE 每题独立启发式)。
- 次选:若想验模型容量·重跑 3B 加 epochs(10-15)到收敛·**需再借 compass GPU**(同流程:请求→让→实测验证 free→跑·跑完 ping 切回·distill_loo 已自动清 adapter 防堆满)。

## 无悬空确认(都已 close)
- ✅ compass GPU 已切回 cuda(close-loop 完整·实测召回满速)。
- ✅ V5 硬盘阻塞已解(datadisk0 99%→69%)+ 机制化防复发。
- ✅ 方向已派 V5(SWE 同质料)。

## 今天 commit(soul turf)
- `210e0fd24` verdict-gate 硬门 wire 进 distill_loo
- `043dde883` expandable_segments 固化(T4 碎片 OOM)
- `bbd5cfafb` LOO 每折自动清 adapter(防 datadisk0 堆满复发)

## 红线沿用
confound 先核再下结论(今天 3 连活样本=没验证结论当定论)· SSH 走 `ssh gpu` 瞬断退避 · 生产改动 grounded + 只删自己的 · 不擅停别框 daemon。
