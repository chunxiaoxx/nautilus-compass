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
| 3 | calibration 四件套 patch+result.md(需求 §3.1;line 682-685 双向预检) | full_score/defective/guessed/equivalent 各 patch+result(8 件) | perfect/deficient/guessed 三目录各 README 占位 | ❌ 命名/格式/件数全不符 |
| 4 | solution/golden/ 子目录(answer.md+change_points.yaml) | 有 | 两件在 solution/ 根,无 golden/ 层 | ⚠️ 层级迁移即可 |
| 5 | variants ≥2 功能等价实现,各过全部 UT(全图 B7/需求 line 158) | variant_a_twopass/variant_b_singlepass | 无 | ❌ |
| 6 | counterexamples 反例程序+真实运行日志(全图 B5/需求 line 125,无法复现直接退回) | py+run.log | 无 | ❌ |
| 7 | tests/assets/selfcheck.md+baseline_runs(需求 §3.1;B4 答卷片段作证) | selfcheck.md 在 assets/ | selfcheck.md 在题包根;baseline_runs 无 | ⚠️ 位置+缺 baseline_runs |
| 8 | 双向预检各连跑 3 次一致(质检 line 682-685) | — | 金/坑各 1 遍(R195) | ⚠️ 补 3 连跑 |
| 9 | 依赖锁定(质检 line 857-869:应用级依赖精确版本/锁文件) | — | 题包无 requirements/lockfile;判分 interpreter 依赖宿主 .venv | ⚠️ 需声明判分环境依赖 |
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
3. **calibration 四件套**:perfect→full_score 改名,补 equivalent 态;各 patch+result.md(逐条打分单)
4. **variants≥2**:helix bridge 功能等价实现 2 份,各过全部 UT
5. **counterexamples**:反例程序+实跑日志(stdout/stderr+版本+平台)
6. **assets 归位+selfcheck 3 连跑+依赖声明**

## 密钥警示(NAS 归档件适用)

题包 environment/workspace/repo/docs 内含 5 月已知泄漏待轮换密钥形态串(GitHub PAT×4+Google OAuth×3,R195 推送事故已剔出 git 追踪,工作区保留)。NAS 归档属组织内网温层可存;**该件任何后续外发/交付前必须先做密钥清洗**。

## 判定证据分层

- 样板题结构/UT 数/score.py 形态:[实测](本档落档时直读 GS-001 实件)
- GS-005 现状:[实测](R195 selfcheck+本轮 find 直验)
- 「打包闸未过」结论:[实测](逐项对照表);补齐后须重跑本核对档全表再启打包
