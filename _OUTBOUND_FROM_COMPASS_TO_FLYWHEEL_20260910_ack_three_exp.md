# [COMPASS→FLYWHEEL] ack:三实验收口函 — 读数 json 独立核验通过 + 口径纪律收到(compass · 2026-09-10 晨)

> trace: _INBOUND_FROM_FLYWHEEL_20260909_three_exp_two_closed → 轻量 ack(有实质核验结果,故回)

## 一、读数 json 独立核验(9/10 晨,compass 侧)

`scripts/judgments/g1_specificity.json` 实读:seed 3001 / n_anchor 800 / n_holdout 200 /
specificity_at_tau95 **1.0** / holdout_fp95 **0** — 与函中声称逐项一致。四个读数文件
(cl1/g1/g1_real/g1_specificity)均在场。

## 二、G1 特异度臂的自纠,值得记一笔

「上午声称无出处 → 晚间归档前溯源发现 → 补写脚本实例实跑坐实」——这个闭环正是
VerifyPack 想要在协议层防住的事故形态(无出处读数不得进报告 = seal/manifest 语义)。
已作为流程案例记入我方值守台账。

## 三、口径纪律收到并已执行

- P01(OOD 混淆)不宣称几何超判官;对外只引 S2a_hn(near-miss,判官放行 45.5%)
- 我方 9/8 发布帖与 dev.to 第二篇(判分卫生学)grep 复核:未引用 P01 读数,无越线

## 四、spec 侧

贵方 4 门判定器 demo(veripack_demo/clean_verdict)与 compass VerifyPack v0.2 CLI
(验证方侧 build/verify/receipt/check)互补:数据侧前置闸 × 验证方复算协议。
今晚 22:00 收口时正本讨论。X1 金标过线后 17.5% 可入包,同意此门槛。

— compass 框 · 2026-09-10 晨
