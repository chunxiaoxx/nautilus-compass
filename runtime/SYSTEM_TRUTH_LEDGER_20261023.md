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

## 🔴 框身份更正(10/24 · 七轮考古教训)

**平台对话框 = nautilus-core 框**(用户口中的"nautilus/平台/最初的对话框"),
其现役历史载体 = `C--Users-chunx-Projects-nautilus-core`(172 条,**永不归档**——10/24 由平台框自愈恢复标准名)。
连字符 live 目录(-Users-chunxiao-wang-Projects-nautilus-core, 838 条)是超集,Mac 路径打开即用。

### 盘整规则新增(血泪条)
> **归档任何 projects 目录前,必须确认无活跃消费者引用该目录名**(进程/长驻 agent/remote 会话)。
> 10/23 归档 C-- core 目录直接断了平台对话框的粮,10/24 平台框自愈改回。同类风险目录逐一排查后才可动。

## 用户叫法 ↔ 实际载体对照表(永不重复七轮考古)

| 您叫它 | 实际载体 | Mac 打开方式 |
|---|---|---|
| **nautilus / 平台 / 最初的对话框** | **nautilus-core 框**(C-- core 目录=平台框本体) | 平台框自管;终端用户 `cd ~/Projects/nautilus-core && claude`(838 条超集) |
| compass / 判读 | nautilus-compass | `compass` 命令 |
| 飞轮 | nautilusflywheel | `flywheel` 命令(2,612 条) |
| v5 | nautilus-v5(最初路径 C:\Users\chunx\nautilus-v5,5/18 起) | `nautilus` 命令(已改指)/ `v5cd` |
| agent 对话框 | Happy 手机会话(主目录) | `cd ~ && claude` / 手机 Happy |
| 台式机上的框 | zenmind = quantum-buddha(禅心 AI = 量子佛陀 V3.5) | quantum-buddha-project 目录 |

## 线务变更(10/23)
- ✅ arm-worker 线退役(拍板;报备函 20974;资产留档可恢复)
- ⏳ fw_api_key 重发函 20972 在途(解锁 flywheel 报备/ack)
- 🟡 v5 OGE 54h 沉默 SLA 危机 → compass 代报备请宽限 48h(21113)+v5 恢复指引(21114)·值守恢复统筹中
- 🚀 深度记忆库全框部署 PASS(12 库 13.9 万块/676MB/零失败)·.db 走 NAS 备份不入 git
- 🔍 阿里基准评测 30 题任务:正本在 agent 对话框(Happy)候用户给原文,组织出题方案已备
- ✅ arm-worker 线退役(拍板;报备函 20974;资产留档可恢复)
- ⏳ fw_api_key 重发函 20972 在途(解锁 flywheel 报备/ack)

## 已知待办(按优先级)
1. 🔴 隧道 launchd 化(重启存活)
2. 🔴 v5 287 脏文件分类(该提交提交/该 ignore ignore)
3. ✅ 6 个核心 launchd plist 已纳仓(ops/launchd/ + install_all.sh,commit 见 git log)
4. 🟡 core/flywheel 各 2 条提交推送
5. 🟢 会话碎片归档(1291 → archive,/resume 清爽化)
6. 🟢 记忆散沙聚类收敛(882 蒸馏 → 主题档案)
