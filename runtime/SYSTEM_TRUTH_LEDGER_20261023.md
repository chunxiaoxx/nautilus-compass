# 系统真相底账(2026-10-23 盘点 · Mac mini 迁移收官后)

> 用途:任何时候怀疑"历史是不是真的/同步了没/配置哪来的",查本文 10 秒出答案。
> 保鲜:值守轮每周重跑三脚本,diff 有变化才更新本文。
> 原则:git 提交 = 唯一可信锚;会话=过程,commit=结果。

## A. 仓同步真相(2026-10-23 实测)

| 仓 | 分支 | 最后提交 | 未推送 | 未拉取 | 脏文件 | 处置 |
|---|---|---|---|---|---|---|
| nautilus-compass | main | 72f9c3df 10-23 | 0(已推✅) | 0 | 1(vtf/fuel_pool) | ✓ |
| nautilus-v5 | master | 0293e5cc 10-23 | 0 | 0 | **287** | 🔴 待分类 |
| nautilus-core | soul-distill-deploy | d3b307d13 10-22 | 2 | 0 | 0 | 候推 |
| nautilusflywheel | main | c0f849f 10-23 | 2 | 0 | 2 | 候推 |

## B. 会话正史(32 个真实对话 · 全清单见 SESSION_LEDGER_20261023.md)

- 总会话 1336 → 碎片 1304(值守轮/测试/蒸馏 worker)→ **正史 32**(9/17 首条 → 10/9)
- 10/10 之后无正史?未鉴定:大量工作发生在手机 Happy 会话(写 C--/live 另册)与 LOOP 轮
- 判据:会话可信 ⇔ 有真实用户消息 ∧(有 commit 或产出物对应)

## C. 配置真相(全清单见 CONFIG_LEDGER_20261023.md)

| 状态 | 项 |
|---|---|
| ✅ 版本化在仓 | v5 bridge .mcp.json / core .mcp.json / round_prompt |
| ⚠️ 不在仓(脆弱) | 13 个 launchd 服务 plist / daemon_env / 全局 hooks / MCP 全局配置 |
| 🔴 无守护 | 隧道两条(19988 反向 / 9877 正向)——**Mac 重启即丢,需建 launchd** |

## 已知待办(按优先级)
1. 🔴 隧道 launchd 化(重启存活)
2. 🔴 v5 287 脏文件分类(该提交提交/该 ignore ignore)
3. 🟡 13 个 launchd plist 纳仓备份(灾难可重建)
4. 🟡 core/flywheel 各 2 条提交推送
5. 🟢 会话碎片归档(1291 → archive,/resume 清爽化)
6. 🟢 记忆散沙聚类收敛(882 蒸馏 → 主题档案)
