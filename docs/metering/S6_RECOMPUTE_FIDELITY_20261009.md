# S6 复算保真度判读(全量 30 例 · 2026-10-09 · R385)

> 复算输入=Round1 A 臂正本 preds(_r181_board30/preds_arm_a.json,30 例);原跑对照=三份分报告(django_report_a+a_eof_report+rest_report_a);复算=cloud swebench 5.0.2 分批 15 批(batch_run.sh 用完即删,零 TIMEOUT)。

## 判读结果

**复算保真度门:PASS(29/30 逐例四桶一致)**

| 桶 | 原跑(三报告) | 复算(15 批) | 判 |
|---|---|---|---|
| resolved | 9 | 9 | ✓ |
| unresolved | 5 | 5 | ✓ |
| error | 16(含跨段重复计) | 14 | ✓(重复计入差) |
| empty_patch | 2 | 2 | ✓ |

**唯一漂移**:django__django-16560 原跑 error → 复算 resolved。方向判读:漂移方向与 Round1 判读层修复口径一致(判读层对格式失败例 reapply 修复后归 resolved 的先例,sphinx-8475 同型 SAME);该例 precise 归因(原跑 error 的具体格式缺陷 vs 复算环境差异)留正式判读卡核,不阻塞保真度判定。

**证据层**:全量四桶读数=[实测](15 份报告文件 /data/s6_rerun/runs/);对照=[实测](三报告逐例);16560 判读层历史=[推断](待判读卡核);复算环境=cloud swebench 5.0.2+分批镜像(判据 sha 不变)。

## 附:交叉验证(10732 v5 件)

v5 交付 R1/R2/R3 三件回归 SQL(不同实现同语义)+双案例预跑基线 DRIFT(-30)/DRIFT(-20)——与本判读独立并行,供 4096 重算验收交叉;本档只判 A 臂复算保真度,五门口径(冲正)另函执行。

—— compass · S6-RECOMPUTE-FIDELITY · PASS · 判读卡候选(编号顺延)
