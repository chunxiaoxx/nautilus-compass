---
name: orgfuel-ORGQ-R89-32ab54040b
description: "### R89 · 2026-10-03 22:5x(exp1 收割判读+exp2 扫描链连跑轮) - **exp1 收"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R89
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R89 · 2026-10-03 22:5x(exp1 收割判读+exp2 扫描链连跑轮)
- **exp1 收割**(全量重训 3ep/lr1e-4,champion 热启动):challenger Δtest=+0.67pt/Δreg=−1pt/**REG-100 金标翻转 6 条**→按预注册判据(Δtest≥+1pt 且 flip=0)**不记首单热启动候选**,负结果如实报。信息量:champion 本训自 train1162,全量重训无新信息只引入优化噪声=**反向实证 P3 增量设计(增益只能来自 delta 新语料)**;loss ep2 0.1268 仍在降→epochs 上扫有据
- **exp2 扫描链发车**(用户拍板连跑):6 组合串行 LR{5e-5,1e-4,2e-4}×ep{3,5,8},预注册判读规则先落盘(Δtest≥+1pt 且 flip≤1=配方候选;全不过线=重训无增益坐实首单等 delta);exp_runner.py 参数化(champion 臂训练前逐条测,flip 精确对齐;修 exp1 的粗 flip 口径);预计 23:40 全链完
- 修 runner 顺序 bug:champion 臂预测必须在训练前(训练改 adapter)——首版放训练后=测错臂,发车前自查抓出
- 下轮第一件:收 exp2 六 summary→汇总表判读;E1 死线 10/5 13:16
- M1:+0(实验线二连跑)
