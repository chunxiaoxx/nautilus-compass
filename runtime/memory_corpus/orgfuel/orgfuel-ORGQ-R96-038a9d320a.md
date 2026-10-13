---
name: orgfuel-ORGQ-R96-038a9d320a
description: "### R96 · 2026-10-04 00:1x-00:4x(exp2 收割轮+E1 判读排障三连) - **exp"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R96
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R96 · 2026-10-04 00:1x-00:4x(exp2 收割轮+E1 判读排障三连)
- **exp2 六件全收割**（预注册第二分支结论生效）:全组合无过线(最接近 exp2b lr2e-4/ep3:Δtest+1.34pt✓但 flip=3✗)→**"重训无增益坐实,首单增益等 delta"**。规律三条:①epochs↑有害(ep5/8 全负,ep8 loss 反弹=过拟合实锤,与 P2v2 早停 ep5 一致)②lr2e-4 方向一致转好(b/e 两组合)但±1.3pt=噪声带级不显著,LR 冻结值 1e-4 不动(只许更严)③loss 最低者读数最差(d:0.0661→−0.67pt)——champion 自训练集到顶,任何重训只引入翻转噪声(P3 增量设计三重反向实证:exp1+六组合)
- **E1 判读排障三连**(链路现已全通):①transformers 5.10.4(v5)无 AutoProcessor→换 openpi venv(4.53.2+cuda ✓)②模型路径 glob 两代缓存布局③blind_data 解析——**samples 本身纯 JSON,原脚本的 replace("'",'"') 是自毁项**(q_pos 内合法单引号被换撞外层双引号),删 replace 即通(n=400 验证)④发车后 **OOM:flywheel gen4_v1 训练(会签线生产件)占 29.7G**——他框域不动,判读排队
- 判读窗口:gen4 释放即发(脚本一KEY就绪);备用路径 4bit/3B 待 SSH 窗口验证 bnb
- 下轮第一件:E1 判读窗口抢占(gen4 释放监控);三外联回应盯守
- M1:+0(exp2 负结果族=配方档案入库)
