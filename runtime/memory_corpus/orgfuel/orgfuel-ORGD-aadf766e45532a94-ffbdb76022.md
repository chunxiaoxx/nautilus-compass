---
name: orgfuel-ORGD-aadf766e45532a94-ffbdb76022
description: "[## 案 3 · pusht 帧级四窗案] - **背景**：pusht 修复效应首判（adapter v2，四窗设计"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-aadf766e45532a94
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 案 3 · pusht 帧级四窗案] - **背景**：pusht 修复效应首判（adapter v2，四窗设计：A1O 存档参照/A1N 干净 orig/A2F 修复 fixed/A2N 同臂双跑）。
- **判据**：帧级辅助读数（dir 率/ratio 带宽/分布），不进层 1 判据本体；效度终判留 rollout（层 1）。
- **材料锚**：四窗 rows_sha16（A1O=`84eb1e39a814c8a0` / A1N=`a50f3e27cd02547f` / A2F=A2N=`afc172f8c4e4a56a`）；噪声底复核：A2F/A2N 推理材料 sha256 全等。
- **判读**：干净对比 A1N vs A2F 样本级显著（Δmedian=+0.24，MWU p=0.03346）；噪声底=0 实测排除 run 噪声；方向支持修复有效（欠幅减轻 0.63 vs 0.39）。
- **claims**：[实测] 样本级显著≠修复归因——帧不配对（各窗各自数据集抽样），抽样混杂未隔离，upgrade_path=配对帧对照（→案 4 执行）；[实测] adapter 变更效应单列（A1O vs A1N p=0.13333 n.s.，时间线混杂实证为代码变更非 run 噪声，A1O 不进数据效应判读——材料方处置正确）；[实测] 全窗 ratio 中位<1=系统性欠幅，模型级现象。
- **边界**：样本级显著与归因级判读分账；pad 占比差异未进判读口径，若入须单列披露。
- **verdict 正本**：`runtime/loop/_p3_pusht_4win_verdict_v2.json`（schema v2 compliant）
- **复算**：`_r61_deploy_pusht_judge.py` → `_r61_pull_pus
