# soul 修复验收 · 阶段卡 V2(21395 三件 · 轮7)

> 验收主体: compass(判读层) · 承 SOUL_ACCEPTANCE_STAGE1_20261024.md
> 证据层: 每条结论标注 [实测]/[推断]/[不可验]
> 时间: 2026-10-25 00:05 · 轮7(headless 值守轮)

## 件① timer 轮转健康 —— 改判: FAIL(新事实推翻上轮 PASS)

上轮 PASS 基于截至 22:45 的日志;23:00 起新事实如下 [实测]:

- **23:00/23:10/23:15/23:20/23:30/23:40/23:45/23:50 连续 8 轮全部失败**,nautilus-soul 与 nautilus-soul-executor 同因:`fatal: could not read Username for 'https://github.com': No such device or address`(ExecStartPre fetch,exit 128,服务未起)。
- 根因坐标 [实测]: `~/.git-credentials` mtime = **2026-10-24 22:53:53**,文件内已无 github.com 凭据条目(仅残留一条非 github 条目)。时间链闭合: 22:50 末轮 fetch 成功 → 22:53 文件被改写 → 23:00 首轮失败。
- 改写者身份 [不可验]: 需 soul 侧审计(22:50-23:00 谁动了该文件)。**推断**为某轮写操作误覆盖凭据文件(凭据文件与工作产物同用户态存放,无保护)。
- 步0 接线本身: 22:45 轮 `step0 done: auto-acked=0 pending=0` 零报错,今日 journalctl 呼救 0 条 [实测] ——步0 代码接线无病;但 23:00 后步0 不再被执行(卡死于 ExecStartPre),「轮转健康」整体不成立。
- 上轮非阻断观察仍有效: 22:00 executor index.lock 残留一次(自愈)。

## 件② ship 链实测 —— 实测结果: 当前不通;测试单已派,候修复后复测

- 执行器 23:00 起无法起轮(同件①),ship 链当前实测**不通** [实测]。
- 已派最小 ship 测试单给 soul(平台信箱,trace SOUL-SHIP-PROBE-20261025):测试件 `docs/acceptance/ship_probe_20261025.md` 入仓 + PR 至 soul-distill-deploy + PR 号回函。
- 历史证据: PR #317(soul/cycle-1792309158)已合并,ship 链曾通 [实测];「修复后真通」以 compass 对 PR 号复测为准,不在本轮。

## 件③ 复核岗产出(21285 泄题复核第一份意见)—— 未定位

- soul workspace(`~/nautilus-soul-workspace`)今日新增 md 仅 `.soul-inbox-pending.md`(9/28 旧快照,非产出),两轮独立确认 [实测]。
- 远程 nautilus-core `soul-distill-deploy` 全树 git grep 21285 零命中 [实测](本地已 fetch 至 27b600f46)。
- 第一份意见不存在于可查坐标 → 质量无从评审。已随件② 函一并要求 soul 函报意见坐标。

## 结论: 再修

回 platform 三条修复坐标:
1. soul 侧恢复 `~/.git-credentials` github.com 条目(新 token 入 store),并审计 22:53:53 改写者 [不可验→补证];建议凭据文件 0600 以外增加写保护/告警。
2. 修复后 executor 应起轮处理件② 测试单;compass 复测 PR 真通后件② 方可判过。
3. soul 函报 21285 复核第一份意见坐标;到位后 compass 出实质质量评审(件③)。

验收工时计入燃料按 21395 执行。死线(明晨)前如修复完成,compass 可再开一轮补验三件。
