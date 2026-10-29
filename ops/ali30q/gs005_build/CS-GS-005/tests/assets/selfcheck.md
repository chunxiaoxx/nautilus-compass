# CS-GS-005 selfcheck 双向预检留证(2026-10-29 · R202 扩条后)

> 位置基准(2026-10-29 R211 归位): 本档落 `tests/assets/`(对齐 GS-001 样板);文内
> `gs005_build/_selfcheck_gs005/`、`solution/…` 等相对路径均自**仓根 ops/ali30q/** 视角书写。

判分解释器: ~/Projects/nautilus-compass/.venv/bin/python(pytest 可用·无 psycopg_pool=坏 DSN 场景走 ImportError 降级)
UT: tests/test_gs005_degradation.py(21 条:targets_badpattern 17 + focus 独立锚 4)
staging 布局 = 容器同构(X/tests + X/workspace/repo,照 task.toml artifacts destination)

| 态 | 构造 | 实跑结果 | 退出码 |
|---|---|---|---|
| Golden(金标) | repo + helix_chain 归位 + 金标 bridge 覆盖 | 21 passed | 0 |
| NOP(坑版原样) | environment 原样(无 helix_chain.py,坑版 bridge) | 21 failed | 1 |

双向留证成立(10/29 R202 轮实测,扩条 3→21 后双向均满幅分叉)。
staging: /tmp/gs005_utexp_pit(轮后可清);复跑命令见缺口档排期与本档表格。
证据副本: gs005_build/_selfcheck_gs005/{golden,pit}(R195 版已清,本轮日志落 selfcheck_*_run.log)。

## score.py 判分入口双态留证(2026-10-29 R205)

复跑(判分解释器=仓 .venv,PKG=本题包根):

```bash
# 坑版态(NOP): 期望 exit 1 / 0 passed
$PY $PKG/tests/score.py --local --tests $PKG/tests --repo $PKG/environment/workspace/repo \
  --out $EV/score_check/ut_matrix_pit.json
# 金标态(Golden): repo + solution/nautilus_core_helix_chain.py → packages/nautilus_core/归位
#   + solution/v5_bridge_golden/helix_bridge.py → v5_bridge/ 覆盖; 期望 exit 0 / 21 passed
```

| 态 | 实跑读数 | 退出码 |
|---|---|---|
| Golden | task=CS-GS-005 passed=21/21 all_pass=True | 0 |
| NOP(坑版) | task=CS-GS-005 passed=0/21 all_pass=False failed=21 | 1 |

矩阵 JSON: _selfcheck_gs005/score_check/ut_matrix_{golden,pit}.json[实测 10/29]。
沙盒分支(/tests→reward.txt)与 GS-001 已过门件同源,容器绝对路径不本地实弹[推断]。

## variants 双实现验证留证(2026-10-29 R211)

solution/variants/ 两份功能等价实现,各过全部 21 UT(staging 同构布局,判分解释器=仓 .venv,实弹[实测]):

| variant | 核算路径 | 实跑读数 | md5 |
|---|---|---|---|
| variant_a_eventlog.py | 事件簿记式:模块级 register_degradation+宿主事件列表,count=len(events) 派生(R207 equivalent 卷升格) | 21 passed | cd493eb8 |
| variant_b_ledger.py | 账本组合式:独立 DegradationLedger 类(独立累加计数器+首事件锚+最新槽位覆盖),degraded/count/report 三面委派派生,outcome=常量字典浅拷贝 | 21 passed | 9b210cbe |

复跑(_staging_calib/ 内,换 impl 后跑):

```bash
git -C staging/workspace/repo checkout -q . && git -C staging/workspace/repo clean -qfd
cp impls/helix_bridge_variantb_ledger.py staging/workspace/repo/v5_bridge/helix_bridge.py
~/Projects/nautilus-compass/.venv/bin/python -m pytest staging/tests/test_gs005_degradation.py -q
```

两卷差异面(与金标三点位对照):降级账结构(事件列表 vs Ledger 类)/计数口径(len(events) vs 独立累加器)/登记形态(模块级函数 vs 宿主私有方法+组合)/outcome 构造(工厂函数 vs 常量浅拷贝);GP-1~GP-4 可观测语义金标/卷A/卷B 三家一致。切段边界与坑版逐字一致。
