# CS-GS-005 结构缺口核对档(2026-10-29 bait 轮)

> 对照正本:nautilus-core/docs/ALI_REQ_STANDARD_MAP_V1.md(B 系列,判读/出题/打包唯一依据)
> + 需求文档 §3.1(line 195-215)+ 质检方案(857-869 依赖锁定/682-685 双向预检)
> + 活样板 CS-GS-001(nautilusflywheel/runtime/fuel_codesense/gs001_judge_1029/pkg/,过平台门实件)
> 结论:**打包闸未过,不打包**。R195 施工件=半边1语义闭合[实测],但距交付结构差六项。

## 逐项对照

| # | 正本要求(行号) | GS-001 样板实测 | GS-005 现状 | 判定 |
|---|---|---|---|---|
| 1 | UT test_* ≥21(需求 line 210) | 23 条(ut_index 23,targets_badpattern 13) | **✅ 已补(R202 10/29):21 条(targets_badpattern 17 + focus 独立锚 4),每条 evidence_required,FM-1~4 全锚,tomllib 门过,双向实跑金 21 passed/坑 21 failed** | ✅ |
| 2 | tests/score.py 判分入口(需求 line 612:全过=1 否则=0,逐条矩阵 JSON) | 有:沙盒→/logs/verifier/reward.txt+ut_matrix.json;本地 --local staging 模式 | **✅ 已补(R205 10/29):移植 GS-001 双模式,本题契约适配(staging=容器同构 staging/tests+staging/workspace/repo,对 UT 的 parents[1]/workspace/repo 单候选定位;TASK_ID 钉死);双态实弹:坑版 0/21 all_pass=False exit1 / 金标 21/21 all_pass=True exit0,task=CS-GS-005[实测];矩阵落 _selfcheck_gs005/score_check/** | ✅ |
| 3 | calibration 四件套 patch+result.md(需求 §3.1;line 682-685 双向预检) | full_score/defective/guessed/equivalent 各 patch+result(8 件) | **✅ 已补(R207 10/29):GS-001 同构平铺 8 件落 tests/calibration/;四态实弹梯度 full_score 21 passed / equivalent 21 passed(事件簿记式等价实现) / defective 5挂16过(挂点=UT-2/13/14/15/21 全消费侧语义,与 GP-2/GP-3 缺漏一一对应) / guessed 21 全挂(病根误诊重试方向);落档件终验复现一致,patch 可应用性 git apply --check 全过,密钥形态串零命中** | ✅ |
| 4 | solution/golden/ 子目录(answer.md+change_points.yaml) | 有 | **✅ 已补(R211 10/29):两件迁入 solution/golden/;实现件(helix_chain/v5_bridge_golden)留 solution/ 根不动(score.py/selfcheck 引用链零破坏,grep 验证)** | ✅ |
| 5 | variants ≥2 功能等价实现,各过全部 UT(全图 B7/需求 line 158) | variant_a_twopass/variant_b_singlepass | **✅ 已补(R211 10/29):solution/variants/ 两份——variant_a_eventlog(事件簿记式,R207 equivalent 卷升格,md5 cd493eb8)/ variant_b_ledger(账本组合式,新写,md5 9b210cbe);两卷 staging 实弹各 21 passed[实测],复跑命令与差异面入 selfcheck.md** | ✅ |
| 6 | counterexamples 反例程序+真实运行日志(全图 B5/需求 line 125,无法复现直接退回) | py+run.log | **✅ 已补(R211 10/29):solution/counterexamples/counterexample_gs005.py(直调被测 repo 真实入口 v5_bridge.helix_bridge,坑版 exit1 TRAP_PRESENT/金标 exit0 FIXED)+三态实跑日志(py 版本+平台[实测]:坑版 4 项静默证据/金标 FIXED/卷B ledger 亦 FIXED)** | ✅ |
| 7 | tests/assets/selfcheck.md+baseline_runs(需求 §3.1;B4 答卷片段作证) | selfcheck.md 在 assets/ | **✅ 已补(R211 10/29):selfcheck.md 归位 tests/assets/(头补路径基准说明);baseline_runs/calibration_four_state_baseline.json 落档(四态梯度 1/1/0.762/0[实测]·模型面候 qwen 渠道修复后补,如实注明)** | ✅ |
| 8 | 双向预检各连跑 3 次一致(质检 line 682-685) | — | **✅ 已补(R211 10/29):Golden 3 连跑全 21 passed/exit0·NOP 3 连跑全 0/21/exit1,双向各 3 次读数逐字一致[实测]** | ✅ |
| 9 | 依赖锁定(质检 line 857-869:应用级依赖精确版本/锁文件) | — | **✅ 已补(R211 10/29):tests/requirements-lock.txt 判分面精确版本(pytest==9.1.1/pluggy==1.7.0/iniconfig==2.3.1/packaging==26.3,dist-info 直读[实测]);psycopg_pool 刻意不装=ImportError 降级题目语义场景,锁文件头注明** | ✅ |
| 10 | task.toml platform 字段(需求 line 258:影响内存/并发的题必填) | — | [environment].os=linux 有,[metadata].platform 无(本题非并发题) | ✅ 可不填 |

## 已达标项(不重做)

- 载体真实:core@9148b7c6d 全仓 1753py 坑版态(>300 门)[实测 R195]
- 坑真实:半边1 defb148 修复证据 git 直验[实测];半边2 候平台坐标如实留白
- UT 锚 badpattern:3 条全 targets_badpattern 对 FM-1~4[实测]
- 双态语义:金标 3 passed exit0 / 坑版 3 failed exit1(R195 selfcheck 实跑)
- task.toml Harbor 1.4 机械字段+编号逐字一致(CS-GS-005)

## 补齐施工排期(候后续 bait/production 轮,每轮一项)

1. ~~UT 3→21+~~(✅ R202 闭合)
2. ~~score.py~~(✅ R205 闭合:双模式移植+双态实弹分叉[实测];沙盒分支 reward 写入与 GS-001 已过门件逐字同源未本地实弹[推断——/tests 与 /workspace/repo 为容器绝对路径,本地不污染根目录])
3. ~~calibration 四件套~~(✅ R207 闭合:四态 8 件+实弹梯度 1/1/0.762/0[实测];等价卷 impls 存 _staging_calib/impls/ 可升格 variant_a)
4. ~~variants≥2~~(✅ R211 闭合:eventlog+ledger 两卷各 21 passed[实测];卷B新写,卷A=R207 equivalent 升格)
5. ~~counterexamples~~(✅ R211 闭合:反例程序+三态实跑日志,坑版 exit1 4 项静默证据/金标与卷B exit0[实测])
6. ~~assets 归位+selfcheck 3 连跑+依赖声明~~(✅ R211 闭合:assets 归位/golden 层级迁移/双向 3 连跑逐字一致/requirements-lock 判分面精确版本)

> **排期全清(2026-10-29 R211)。全表 10 项 ✅(第 10 项 platform 可不填维持原判)。**
> **✅ R214(10-29)全表复核通过+打包闭合**:全表逐项直验(tomllib 门 PASS·ut_count=21/ut_index 21/targets_badpattern 17·score.py 双模式·calibration 8 件·golden 两件·variants md5 cd493eb8/9b210cbe 与档一致·counterexamples 三态日志·baseline 梯度 1/1/0.762/0·requirements-lock 4 件精确版本)+清洗后双向复跑(NOP 0/21 exit1·Golden 21/21 exit0)与 R211 基线逐字一致[实测]。**打包**:pkg/CS-GS-005 密钥清洗(14 文件 23 处灭活:首轮 21+GOCSPX- 自匹配 token 修正 2,日志 secret_scrub_log_20261029.md)→ tar 30M md5=8ee99a3823ba6b9a6af7a45658254795 → NAS shared/codesense_real_lesson/CS-GS-005_v1_1029_clean.tar.gz(端到端 md5 一致)+README_唯一有效包.md 增 CS-GS-005 节。原始未清洗件仍仅存仓内 gs005_build/CS-GS-005(git 13 密钥件剔除态不变),pkg/ 与 tarball 已加 .gitignore 护栏。交付/发函动作候用户与平台编排,本轮不外发。

## 密钥警示(NAS 归档件适用)

题包 environment/workspace/repo/docs 内含 5 月已知泄漏待轮换密钥形态串(GitHub PAT×4+Google OAuth×3,R195 推送事故已剔出 git 追踪,工作区保留)。NAS 归档属组织内网温层可存;**该件任何后续外发/交付前必须先做密钥清洗**。
> ✅ 2026-10-29 R214:交付副本(pkg/+NAS tarball)已按本条清洗完毕并复验零命中;本警示对仓内原始工作副本继续有效。

## 判定证据分层

- 样板题结构/UT 数/score.py 形态:[实测](本档落档时直读 GS-001 实件)
- GS-005 现状:[实测](R195 selfcheck+本轮 find 直验)
- 「打包闸未过」结论:[实测](逐项对照表);补齐后须重跑本核对档全表再启打包
