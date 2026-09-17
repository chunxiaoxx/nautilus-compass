# 首考判卷 · 门1 读数(2026-09-18 晨 · 判分器=官方双门语义,scripts/assay_gate1.py)

官方语义(v5 f1cb5ea 工具):门1=worktree@buggy_commit+verifier 取 fix 版覆盖→pytest 必须 FAIL。

| 题 | 仓 | buggy | 门1 读数 |
|---|---|---|---|
| a3795c2f8ea9 | v5 | 0ad9b912740b | rc=1 · 1 failed ✓必败 |
| 355a214f29d4 | v5 | b0331f195ccc | rc=1 · 1 failed ✓必败 |
| 914b39c7bdea | core | 34215951629a | rc=1 · 1 failed ✓必败 |
| 37a117f093ec | core | dc29a008a770 | rc=2 · 1 error(collection error 形式过门,按官方 rc≠0 语义计;成绩单备注)|
| 0c2c60c7a115 | compass | 5f77f1a52ff4 | rc=1 · 1 failed ✓必败 |

**门1 计:5/5 必败成立。** 参照正解门2 抽验(37a1,胶囊自证):16 passed ✓
(pathspec 坑复现官方 QC 同案并修复:测试目录排除须含 `*/tests/**`)。
待 v5 produced diff → 真门2(fix 后必过)+门3(diff 不动测试)。
