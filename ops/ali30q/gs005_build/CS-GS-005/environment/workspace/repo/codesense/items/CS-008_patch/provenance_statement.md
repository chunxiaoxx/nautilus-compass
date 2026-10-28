# CS-008 Provenance Statement(来源声明·VV-25 补证)

## 题目溯源

- **载体**:OCR 数字列清洗核验(ocr_pipeline,列级置信度与清洗纪律,Python)
- **badpattern 机制**:清洗纪律违反(低置信处理/列对齐校验/逐列核对范围——对应甲方 P6 范围遗漏漏项与 P1 口径语义错位家族)
- **场景来源**:数据清洗真实工单复现(置信度阈值绕过导致脏数据入库类事故)——非虚构

## 构建时序声明(UT 先于答卷)

1. 坑版+修复版双态实现先行(git 可溯)
2. UT 设计与冻结先于任何模型答卷(A 批原校准 10-18~19 落盘)
3. 嵌仓返修(10-24):真仓库语境嵌入,manifest 与校验和齐
4. **本题为 A 批早期产物,流程未定型期产出——如实声明**;补强措施:反幻觉内嵌段(§前置复核)已按 10-24 定稿范式补写(平台代笔稿 codesense/items/CS-008_patch/,候产线采纳),配套 gating UT 断言同步补

## 证据坐标

- 四门校准:tests/calibration/(四套件)
- 嵌仓 manifest:codesense/dist/batch_A_manifest.csv(CS-008 行)
- 构建轨迹总纲:codesense/dist/BUILD_TRAJECTORY_A_BATCH.md
- 交付包 sha16:7edd3ca7(嵌仓返修版)

## 声明

本声明由生产方如实撰写,构建记录可由 git 历史与落盘时间戳交叉验证。
若需求方对任一证据坐标存疑,我们提供原始仓库只读访问配合核验。

—— 上海国曙智能 · CodeSense 题库产线
