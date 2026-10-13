# 触发池四臂对照判定卡(2026-10-13 · R530/R531 · 同池同切分同配方)

> 语料=触发池 5045ff1235e345e6(train 2543 / holdout 300,自举标签 63.7%);
> 全部臂同 holdout 300 对拍,读数横向可比;现役基线=1.7B champion(1454 人工标签训练,sha16 dbcbab6fd1ff5821)。

## 一、四臂读数表 [全部实测]

| 臂 | 基模 | acc | vs 现役 | 裁定 |
|---|---|---|---|---|
| 现役 champion | 1.7B(人工标签 1454) | **0.9667** | — | **保持现役** |
| 8B 触发臂 | 8B bf16 | 0.9767 | +1.0pp | 不升格(G1 门 +2.0pp 未达,SEVENB_COMPARE_PREREG) |
| **1.7B-v2 重训臂** | 1.7B bf16 | 0.9467 | **-2.0pp** | **不切换(U5 不劣门 FAIL,RETRAIN_PREREG)** |
| 4B 观察臂 | 4B bf16 | ⟨挂起⟩ | ⟨—⟩ | 观察位不裁定;**基础设施阻塞挂起**(A100 磁盘配额顶格 98%,modelscope 双片 ENOSPC+Range 续传挂+hf-mirror 启动败三连;解法=跨框协调清理具身侧资产或经云端中转,非 compass 单方面可解;骨架已备,基模就位后随时补跑) |

## 二、合成结论(三条读数链)

同池同配方,唯一变量=容量:**8B +1.0 / 1.7B-v2 -2.0 / champion(人工标签)0.9667 最强。**

1. **自举标签(63.7%)对小模型是净伤害**:1.7B 在自己产的标签上重训反而降 2pp——回声室效应实证;
2. **容量可部分吸收标签噪声**:8B 同池 +1.0pp(正增益),但不足跨尺寸升格门;
3. **标签质量 > 数据量**:champion 用最少的数据(1454)拿最高分,因为标签是人工的。

## 三、下一杠杆(证据驱动)

**人工抽检自举标签**:从 1811 条自举标签抽 100 条人工复判,测 judge 自判准确率(定池子置信区间)。
若 judge 自判 ≥95%:自举标签可用,棘轮继续;若 <90%:标签回灌修正后再训。
**顺序:先提标签质量 → 再扩标签 → 再重训。顺序反了就是回声室(本轮 1.7B-v2 实证)。**

## 四、执行细节与披露

- 两预注册档均出数前冻结:SEVENB_COMPARE_PREREG(G1 +2.0pp)/ RETRAIN_PREREG(G2 margin 1.0pp=跨尺寸之半,同尺寸重训口径)
- qid 防泄漏:三臂训练 qid 交集全部 0(8B 臂首跑 73 交集被门拦截后同构化重切)
- 自举标签 63.7% 知情披露;读数为相对增益非绝对正确率
- 4B 臂为观察位不参与裁定(RETRAIN_PREREG 约定);4B 若降=噪声主因坐实,若升=容量主因

## 五、复算坐标

- 8B:judge8b_trigger_20261013_upgrade_report.json + eval300 双文件
- 1.7B-v2:retrain_17bv2_20261013_upgrade_report.json
- 4B:⟨待收,/root/vdf/retrain_4b_out/upgrade_report.json⟩
- 切分审计:runtime/verdict_corpus/eightb_trigger/split_audit.json(双 sha)
- 脚本:_train_judge8b_trigger_A100.py / _train_retrain_17b4b_A100.py / eightb_trigger_split.py

—— compass · 四臂对照 · 2026-10-13 · 负结果照报
