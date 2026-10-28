# CS-003 Provenance Statement(来源声明·VV-25 补证)

## 题目溯源

- **载体**:星历时管精度缺陷核验(ephem/ 子系统,astropy 天文计算库语境,Python)
- **badpattern 机制**:精度漂移/存储格式语义(JD double 有效位数 vs ISO 字符串精度)
- **场景来源**:OBS-772 真实事故复现(观测时间戳微秒位丢失)——非虚构

## 构建时序声明(UT 先于答卷)

1. 坑版+修复版双态实现先行(git 可溯)
2. UT 设计与冻结先于任何模型答卷(A 批原四门校准 10-18~19 落盘,早于 _s5 基线答卷)
3. 嵌仓返修(10-24):astropy 全量语境嵌入,文件数与校验和见 manifest
4. 例外声明:A 批早期曾在 S5 后补 UT——当时流程未定型,10-24 起新题全部按"UT 冻结于 S3"时序

## 证据坐标

- 四门校准:tests/calibration/(perfect/equivalent/deficient/guessed 四套件)
- 嵌仓 manifest:codesense/dist/batch_A_manifest.csv(CS-003 行)
- 构建轨迹总纲:codesense/dist/BUILD_TRAJECTORY_A_BATCH.md
- 交付包 sha16:9256cb0b(嵌仓返修版)

## 声明

本声明由生产方如实撰写,构建记录可由 git 历史与落盘时间戳交叉验证。
若需求方对任一证据坐标存疑,我们提供原始仓库只读访问配合核验。

—— 上海国曙智能 · CodeSense 题库产线
