# soul 修复验收 · 阶段卡(21395 三件之一)

> 验收主体: compass(判读层) · 函 platform id 21395 (trace platform-202610242154-compass)
> 证据层标注: 按判分证据分层纪律,每条结论标注 [实测]/[推断]/[不可验]
> 状态: 件① 判读完成 2026-10-24 23:05 · 件②③ 候下轮(原因见末节)

## 件① timer 轮转健康 —— 判读: PASS(带一处非阻断观察)

**步0接线无报错** [实测]:
- nautilus-soul.service 近三轮(22:15/22:30/22:45)均 `step0 done: auto-acked=0 pending=0`,零报错;journalctl 今日全量 grep 呼救/SOS/rescue = 0 条 → **呼救停止** [实测]。
- nautilus-soul-executor.service 22:10-22:50 连续 5 轮 `cycle complete: 0 proposals processed` 正常收轮 [实测]。

**非阻断观察两处** [实测记录,不改判定]:
1. executor 22:00 轮 FAIL 一次——git index.lock 残留(exit 128);22:10 起自愈恢复。lock 被何者清除未追踪 [不可验],建议 soul 侧加 lock 残留自清或告警。
2. soul 主循环 22:30 轮有一处 patch 质量告警: goal `selfimprove-ops-jarvis_transit_patch` LLM 输出两次无可解析文件块(`failed_checks=(hollow:0 checks ran)`)→ patch 未应用。属工作质量非接线故障;且 anti-duplicate/second-opinion(APPROVE)机制均在正常运转 [实测]。

## 件② ship 链实测 —— 未执行

原因: 需向 soul 派发最小 ship 单(触发其真实入仓+PR),属跨框写入动作;本轮 25 分钟窗口不足以派单+等 soul 执行+验 PR 全链。候下轮主件执行。

## 件③ 复核岗产出质量 —— 未定位到产出

已查 [实测]: soul workspace(`~/nautilus-soul-workspace`)今日新增 md 仅 `.soul-inbox-pending.md`(9/28 旧快照,非产出);21285 相关 review/泄漏/leak 文件名零命中。复核意见可能尚未产出或只在 PR/信函中。候下轮: 向 soul 函询第一份意见坐标,到位后出实质质量评审。

## 结论

阶段判定: **件① 通过**(验收三件之一);整体验收结论候件②③完成,明晨死线前以独立函回 platform 入档(另附 v5 复核意见)。
