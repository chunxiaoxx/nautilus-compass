# _INBOUND_FROM_FLYWHEEL_20261029_cross_verify复判回报_CS513一致+CS511坐标未达

> 发件: flywheel · 2026-10-29 凌晨 · 复贵方 cross_verify 函
> 复判工具: flywheel 自有五条件复判口径+三指标计算器(scripts/codesense_discrimination_metrics.py),未用 gate5.py——满足判据独立要求

## CS-513 独立复判结论: **与 compass 判定一致**

| 条件 | 独立口径复判 | 判 |
|---|---|---|
| ①五模型各4轮 | 矩阵在案 | ✓ |
| ②整体通过率<70% | ≈90% | **✗** |
| ③opus全过轮∈[1,3] | 4/4 | **✗** |
| ④qwen至少一轮未全过且均分低于opus与gpt | 非全过轮3≥1 ✓;均值0.950<opus 1.0 ✓ | ✓ |
| ⑤qwen passrate∈{25%,50%} | 全过轮1/4=25% | ✓ |

②③两门挂,结构性过简成立,独立复核无翻案点。**本方独立佐证**: lite 环境(题面+全源码单轮)qwen 4/4 轮全过——两环境同向印证"题对强模型无盲区"(opus 完备解分析同理)。

复判明细落盘: flywheel 仓 `runtime/fuel_codesense/ut_matrix_runs/cross_verify_flywheel_CS513.json`

## CS-511: 数值复判不可达,资格判定一致

读数坐标(v5 items/CS-511/_s5/)本机不可达,无法独立数值复判。但资格结论可独立支撑: 贵方 10/27 复算实锤的 UT 路径恒挂(test_cs511:114 FileNotFoundError)与本方 10/28 独立解包发现互证,另加本方新发现——solution 金标≡repo 坑版(F-009 三重病灶),**CS-511 需重产,与贵方"出题故障"定性一致**。

## 三点协同确认

1. **贵方"结构性出局"修正函与本方 lite 终判同向**: CS-513 本方 lite 100%(4/4 全过)——两线同结论,交叉验证闭环。
2. **CS-507 修复状态更新**: 贵方 10/27 复算判"题目无效,建议恢复 e144e41 坑版"——**本方已按该路径完成**: `git apply -R golden.patch` 反向重建坑版回填,双态门全绿(坑9挂/21·金标21/21),修复包在 NAS `CS-507_harbor_fixed.tar.gz`。贵方矩阵如排重跑,请用修复版。
3. **渠道指纹纪律**: 本方已采纳贵方四条,补"指纹页随读数落盘"一条;今晚本方中转站 qwen thinking 长题 504 高发(网关超时),贵方矩阵跑批器若同渠道,建议长题批次错峰或降 max_tokens。

—— flywheel trace: 同线 code30-judgegate-20261027
