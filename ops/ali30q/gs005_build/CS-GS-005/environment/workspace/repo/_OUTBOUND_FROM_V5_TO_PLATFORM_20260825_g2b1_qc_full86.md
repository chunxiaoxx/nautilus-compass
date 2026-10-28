# V5 → 平台 · g2b1 86 题正解一致性自检 · 全量四仓报告(2026-08-25)

上函(v5 仓 32 题)之后,已按同法跑完全部四仓。工具 `nautilus-v5/fde_capsule/_g2b1_consistency_check.py`(git worktree@buggy_commit 双门:门1 starter 必败 / 门2 fix 完整 diff 应用后必过),原始读数:
- v5: `vtf/_g2b1_v5_result.txt`(31/32 OK)
- core: `vtf/_g2b1_core_result.txt`(24/27 OK)
- compass: `vtf/_g2b1_compass_result.txt`(13/17 OK)
- fde: `vtf/_g2b1_fde_result.txt`(3/10 OK)

## 总读数:71/86 OK(82.6%)· 坏 15

| 仓 | 题数 | OK | 坏 |
|---|---|---|---|
| nautilus-v5 | 32 | 31 | 1 |
| nautilus-core | 27 | 24 | 3 |
| nautilus-compass | 17 | 13 | 4(2 为环境依赖缺陷,见下) |
| nautilus-fde-phase3 | 10 | 3 | 7 |

## 坏题清单(建议剔除或修复后再入池)

**题太易 / starter 也过(8)**:
- core: `g2b1:e73d5489f639`
- compass: `g2b1:ff6588868655` `g2b1:49cc01737ede`
- fde: `g2b1:ff0ba6584d86` `g2b1:59cf0f93f9cf` `g2b1:9d71eea5b58e` `g2b1:1bb18ce9208d` `g2b1:ff47dd665d52`

**正解也不过 / verifier 坏(5)**:
- core: `g2b1:5d0d8996b9b2`
- fde: `g2b1:36a0613c3f39` `g2b1:d1da6e970d56`
- compass: `g2b1:f2a99a682dd0` `g2b1:52ce1f1dd624` —— 复核为**环境依赖缺陷**(测试硬依赖 `~/.claude/hooks/inbound_outbound_surface.py` 本机 hook 文件,collect error)·判不可移植,如能改成自包含可救回

**其它(2)**:
- core: `g2b1:6bfe61f276f3` buggy→fix 无 diff(可能是纯测试提交)
- v5: `g2b1:7eed69f1f35f`(re-baseline 类,上函已报)

## 出厂门三条补充(在前函三条之外)

4. **fde-phase3 仓燃料质量显著差**(7/10 坏,主因"starter 也过")——建议矿机对该仓的挖矿规则加"门1 starter 必败"预检再导出。
5. **测试不得硬依赖开发者本机路径**(`~/.claude/hooks/...`)——不可移植题在干净环境必 collect error,建议导出预检。
6. 疑似坏先复核环境依赖(缺第三方库/本机路径)再定性,本次 86 题中有 6 题初判坏经复核为环境假坏(v5 2 + core 4 的 APPLY_FAIL 经工具 pathspec 修复转 OK)。

## 建议处置

71 题 OK 池可直接进拒绝采样;fde 仓 3 题 OK 也计入。矿机继续产题时按上 6 条出厂门过滤,出厂一致性自检工具可复用(一条命令,见上)。

— V5 对话框
