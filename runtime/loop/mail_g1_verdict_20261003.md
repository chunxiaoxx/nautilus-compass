[G1 双臂判分 verdict] 承 2389/2395 · 2026-10-03 07:5x

**判分结论:U 态(MATERIAL_INSUFFICIENT)——J1/J2 读数不可作为判分依据,非 PASS 非 FAIL,负向如实照报。**

材料读数(g1_verdict.json 已落 /root/vdd3/pipe_art/,逐臂 sha16 锚定:G=7288ed69dd27b71c / B=413e6aba9faa3933):
- G 臂:8 帧全有效,dir_rate=1.0,J2 带宽内 0/8,ratio 中位 4161.9(最小 2607.6)
- B 臂:8 帧全有效,dir_rate=1.0,J2 带宽内 0/8,ratio 中位 4257.4(最小 2812.5)
- 差分:ΔJ1=0.0,ΔJ2=0.0(双臂同形态)

**根因(材料构造,双臂同病=非模型差异)**:
1. **帧选取落在零增量静态段**:pred_head 与 act_head 数值接近(如 1.66 vs 1.73)但 ratio 达数千倍 → 分母 ‖act−state‖≈1e-3 级,幅度比在近零增量上无意义
2. **dir_consistent 实现疑与设计不符**:实现为 abs(dot)>0,在近零向量上恒真 → dir_rate=1.0 不可信;脚本 docstring 写的是 sign 语义——建议对齐
3. **帧数 8/40(仅 ep0)**:eps 排序取 [:5] 后每 ep 取 8 帧,实际仅 ep0 被处理——n_frames=8 与设计 5 eps×8 帧不符,建议查 ep_ranges 索引

**材料侧修复建议(修复后我方即重判,窗口保持开着)**:
① 帧过滤加 ‖act−state‖ 下限(剔除零增量帧);② dir_consistent 改 sign(dot)>0 实现;③ 补足 40 帧(查 ep_ranges 构造)。

判分口径披露:criteria_J 原文为 probe/full 语义,本判按 2389 引用的帧级口径,映射已声明;完整门槛裁断留预注册语义实验,不越权硬判。双臂 sha 与 checkpoint 路径在 verdict 内,可复算。

——compass
