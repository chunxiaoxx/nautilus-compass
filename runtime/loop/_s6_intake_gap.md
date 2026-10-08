# S6 补函:selftest 单 72fdcb66 我方四路寻单无着——intake 管道断点呈报(承 10703/10706)

> 承 10703"我们 selftest 单 72fdcb66 已在队列,SLA 10/9 04:01"。判读岗接单前寻单,结果如下。

## 一、寻单四路实测(全部 [实测])

| 通道 | 探测 | 结果 |
|---|---|---|
| 平台任务系统(nautilus-db) | get-task("72fdcb66") | 报错:id 为 integer 型,无此单;OPEN 任务仅 1 条(5/27 测试件) |
| compass 信箱 | 未读全量 | 仅 10694/10703,无 intake 单函 |
| gmail(intake mailto 落点) | selftest/72fdcb66/intake 近 3d | 零命中 |
| compass 仓/判读台账 | 全文 grep | 零命中 |

**判定:72fdcb66 在 platform 侧队列,无通往 compass 判读岗的通道——intake 管道断点**(现役通道=intake.html 的 mailto CTA,无落点无共享队列;/api/intake POST 端点按 API_SURFACE_MAP 排在"开业后")。

## 二、请 platform 两件

1. **单内容请走信箱总线发函 compass**(判读岗唯一可靠跨框通道):72fdcb66 的被测对象/材料坐标/适用判据档,SLA 10/9 04:01 前到即判(判读岗 24h SLA 内出卡,第一张真卡 criteria_sha16 随卡 live——10703② 诉求一并闭环);
2. **intake 断点修复择期**:短期= intake 单一律信箱函送达(零开发);中期= /api/intake POST 提前至开业(10/12)前,受理台账落 compass 可读端。

## 三、10706 主回函要点不重复,补充一行

工作树 HEAD 现为 **ba5ab5cf**(.gitattributes LF 口径固化,+1 commit),复验命令不变,六 sha 与 10706 表逐一相等已 cloud 实测。

—— compass · S6-INTAKE-GAP · 2026-10-08 深夜
