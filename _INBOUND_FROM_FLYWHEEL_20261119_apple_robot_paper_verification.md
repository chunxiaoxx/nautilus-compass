# 飞轮 → Compass：苹果机器人论文核验交接

日期：2026-11-19  
性质：论文研究材料入站；论文正文、引用和投稿由 Compass 决定。

## 核验范围

本地未找到用户本轮上传的具体附件。当前按官方页面和 arXiv 原文核验三条最可能路线：

1. **HALO — Perceptive Humanoid Motion from Simulation**，arXiv:2611.06908；
2. **AMP1 — On Agentic Manipulation Policies**，arXiv:2611.09892；
3. **ARMOR / EgoDex**，Apple ML 官方页面。

飞轮事实报告：

`runtime/reports/apple-robot-paper-verification-20261119.md`

## 当前事实边界

### HALO

- 约 1,000 个程序生成住宅、约 300 小时合成 episode；
- VLM 约 0.5 Hz，运动生成器约 3 Hz，跟踪器 50 Hz；
- 论文报告 6 个未映射真实环境、360 次真实试验、单技能约 91% 成功率；
- 长链成功率低于单项成功率乘积；
- 生成前包含运动约束、场景碰撞筛选和多项几何检查。

**不能从中推出**：开放世界泛化、自动发现新技能、独立复现或通用 scaling law。

### AMP1

- 通用模型通过 persistent interpreter、SDK、机器人服务器和 harness 直接控制机械臂；
- 论文报告 RoboLab-120 85.6%，108 次真实 trial 中 104 次成功；
- 持久记忆在特定 RoboDojo 任务上降低失败率；
- 强模型直接控制基础 harness 的表现优于部分辅助 routine。

**不能从中推出**：通用安全、无验证控制或垂直模型已经被完全替代。harness 的动作边界、碰撞和结果判定仍需独立验证。

### ARMOR / EgoDex

- ARMOR：约 86 小时 AMASS 人类动作，仿真碰撞规避和 Fourier GR1 部署；官方报告碰撞、成功率和延迟改善，但完整任务数、seed、碰撞定义、置信区间、真机对照和代码仍需回读；
- EgoDex：829 小时第一视角视频、194 个桌面任务、同步 3D 手/手指追踪，主要是人类手部轨迹预测。

EgoDex 属于压缩/数据端证据，不能直接写成机器人迁移；ARMOR 属于感知/仿真策略端证据，不能直接写成 RSI 或通用泛化。

## 对 Compass 理论线的交接判断

```text
EgoDex：人类 ego → 手/动作 latent                    压缩端
HALO：仿真 → 视觉-语言-运动 → 真机                   仿真/执行端
AMP1：通用模型 → harness → 机器人                   候选生成端
飞轮：独立判据 → 反事实挑战 → 真实 holdout            验证端
```

建议 Compass 在论文中保留三层区分：

1. 论文作者自报结果；
2. 工程上可回放的仿真或真机证据；
3. 经过独立复算和真实消费者读回的验证结论。

本函不要求飞轮继续编辑论文正文；只把事实、边界和证据坐标交给 Compass。
