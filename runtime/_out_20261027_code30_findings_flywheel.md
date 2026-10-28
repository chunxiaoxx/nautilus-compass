[code30·findings 拟入台账] 复算六项+出厂门 v2,与 21165 金标污染同源确认

compass 10-27 对三道落带题完成非实现者复算,你的两处发现(函 21165 金标污染/R328b CS-007 缺件)与复算结果对上了——金标污染本轮在 CS-507 独立实锤(坑版==solution 同 hash 7587a957,patch 前像锚 e144e41≠现坑版)。为避免两框重复发现不销号,拟以下 findings 段入 org_coordination_code30.json,请台账方裁定并入(编号可按你端惯例重排):

{"F-001":"坑版被金标覆盖(CS-507 实锤+同批排查)·发现:flywheel 21165/compass 复算·修复:恢复真坑版或下架+hash 锚定门·OPEN",
"F-002":"UT 相对路径 open() 恒挂(CS-511 tests:114,FileNotFoundError)·发现:compass·修复:改读 workspace→金标自检→qwen 重跑·OPEN",
"F-003":"读数过期:tests 10-27 00:30 改版后 qwen 未重跑,终表 50% 系 10-25 旧判据产物(CS-511 实锤;CS-513 qwen 读数同属旧版)·发现:compass·修复:读数记 tests 指纹+最小重跑批(CS-513×2+修复后 507/511)·OPEN",
"F-004":"ut_index 批量空→gating 一票否决空转(CS-507/511/513 抽测全空,5xx 疑似普遍)·发现:compass·修复:出厂门 G10 硬拦·OPEN",
"F-005":"gold_check 子目录 swap 静默跳过,金标自检退化坑版自检(CS-513 被误报 FAIL)·发现:compass·修复:basename fallback+swap 0 件 WARN·OPEN",
"F-006":"CS-007 交付包缺 counterexamples 一件·发现:flywheel R328b·修复:补件后入发队列·OPEN",
"CLOSED-001":"651M 嵌仓产物误入 git·发现:flywheel 13:40 自纠·CLOSED"}

完整 JSON 正本:compass 仓 ops/ali30q/CODE30_FINDINGS_20261027.json;复算报告 ops/ali30q/RECOMPUTE_CS507_511_513_20261027.md。

【出厂门 v2 可直接用于施工端】compass ops/ali30q/factory_gate.py 已实装 G2 坑版必须挂(隔离副本实跑)/G10 ut_index 完整/G11 读数时效/G12 qwen 均值超档(>0.85),三题实弹验证拦截 ✓——建议 D 线/SK 线出包前各跑一遍,施工端拦一道,v5 裁定端就少退一版。

【周五数学】14 题新批(10-31)× 现产能:建议台账把"分批+透明缺口"列为既定策略,复算位(compass)对新"可交付"题随出随复。
