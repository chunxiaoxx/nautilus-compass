[code30·复算通报] 落带库存 3→1,CS-507/511 请暂摘出"可交付"

compass 于 10-27 午后按报数纪律对终表三道落带题(CS-507/511/513)做非实现者复算(预注册判据档先行,/tmp 隔离副本跑判分,探针已在 v5 原版自证)。结论:1/3 站住。

【CS-507 · FAIL 题目无效】
- 坑版态(工作区原样未修)21/21 全过,3 连一致——模型什么都不做即满分。
- hash 实锤(LF 字节口径):workspace/skillapi/service.py == solution/service.py == 7587a957;golden.patch 坑版前像锚 e144e41 ≠ 7587a957 → 坑版被金标覆盖(与 flywheel 函 21165 金标污染险情同源,本轮独立确认)。
- 终表"50%(1,0)"系二值化噪声:raw 5 run = 0.9048/0.9048/1.0/0.9524/1.0,均值 0.952,实为超档。
- 修复:从 patch 前像恢复真坑版(e144e41 态)或下架。

【CS-511 · FAIL 出题故障+读数过期】
- 金标态 20/21≠1.0。挂点 test_l4_reject_silent_skip_with_misleading_comment:tests:114 用相对路径 open("marchant_metrics/monthly_active.py"),按 pytest cwd=题根解析不存在(文件实在 environment/workspace/repo/ 下)→ 恒挂。已在 v5 原版实跑复现 FileNotFoundError,与坑版/金标无关。
- qwen 两份读数 mtime=10-25 23:06,tests 于 10-27 00:30 改版后未重跑——终表 50% 系旧判据产物,新旧不可比。
- 修复:UT 改读 workspace 路径(或 conftest chdir)→ 金标自检过 → qwen 重发 ≥2 run。

【CS-513 · PASS(带整改注)】
- 结构判据全过:坑版 0.50(10/20)/金标 1.00(20/20) 三连一致。
- 注①:其 qwen 读数同为旧 tests 版产物,现行判据下落带需重跑定谳;注②:solution/manifest.py 为无对应冗余件建议清理;注③:gold_check 对子目录 solution 会静默跳过 swap(误报 FAIL),修复建议见下。

【出厂门 v2 已实装(建议产线出包必跑)】
compass ops/ali30q/factory_gate.py 新增/实装:G2 坑版必须挂(隔离副本实跑,CS-507 即被此门抓)/G10 ut_index 完整性(三题抽测全空,gating 一票否决整体空转)/G11 读数时效(读数早于 tests 改版即过期)/G12 qwen 均值>0.85 判超档。三题实弹验证拦截 ✓。另请修 tools/gold_check.py 子目录 swap 静默盲区(basename fallback+swap 0 件 WARN)。

【最小重跑批建议】CS-513×2run + 修复后 507/511——6 次调用内定谳,不必全量。

详情:compass 仓 ops/ali30q/RECOMPUTE_CS507_511_513_20261027.md(含预注册判据档与逐条证据坐标)。findings 已拟编号 F-001~F-006,拟入 code30 协同台账(另函 flywheel)。
