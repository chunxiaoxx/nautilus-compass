# LME-V2 榜单提交就绪度盘点(2026-09-21 · B 类默认值提前件)

> B 类默认值「LME-V2 提交(默认 9/22)」——今日先把材料盘点与缺口清出来,
> 表单提交按默认值明日执行。attribution 纪律:N6 T0 路线=官方基准成绩册+判分
> 协议+调优栈(451 题=上游 xiaowu0162 官方基准,非自建,提交署名如实)。

## 提交通道与规则(官方 README 实读)

- 通道:**Google 表单** https://forms.gle/rxUpiuRKDERqpqSi9 ——**明确不接受 GitHub
  issue 提交**(informal issues 会被关闭/删除;我们 9/17 的 #13 是借轨合作函,不冲突)。
- 打包规范:leaderboard/README.md——一次提交=**一个 memory 方法 × 一个 tier**
  (small/medium),可含多个延迟工作点;每个工作点=**一对完整 run(web+ent)**,
  helper 合并出 6 指标:overall_full_set / gotchas / static / dynamic / procedure
  accuracy + memory_query_avg_seconds;最终 LAFS gain 对固定参考前沿
  (accuracy=overall×100,latency=query 均秒)。

## 我方材料盘点

| 件 | 状态 | 坐标/缺口 |
|---|---|---|
| 成绩(d12 现役·d14 干净口径) | ✅ | web 40.0% / ent 38.4%(451 题全量;judge=doubao 协议披露在案) |
| 五分解 accuracy(gotchas/static/dynamic/procedure) | ⚠️ 部分 | d12 复盘有 static/dynamic 读数;gotchas/procedure 分解需从原始 run 重导 |
| per-query 延迟(memory_query_avg_seconds) | ❓ | tests/bench_profile.{sh,ps1} 可测;451 题原始 run 是否已带延迟记录待查 |
| 双域原始 run 文件(web+ent 各一对) | ❓ | GPU 机已退租;归档位置待查(本地/云;TRANSFER_RUNBOOK 有复跑命令) |
| tier | ✅ | small(451 题口径) |
| 方法名 | ⚠️ 待定 | 建议 nautilus-mem;与命名纪律一致(对外全名,勿撞 CompassBench) |
| 参考前沿 LAFS | ✅ | 官方 helper 计算(fixed reference frontier 随仓) |

## 明日执行序(默认值生效即跑)

1. 查原始 run 归档(本地 runtime/ 与云归档两处);缺则按 TRANSFER_RUNBOOK 复跑
   (GPU 复用纪律:先查保留盘)。
2. 用官方 leaderboard helper 组 operating point 对+LAFS 包。
3. 表单提交(forms.gle 需浏览器=用户 1 分钟动作;或 curl 模拟,失败则请用户代点)。
4. 提交后回执:无(表单)——以提交确认截图/邮件入档,判分协议披露随附。

## 边界

- 提交=「成绩上官方榜+判分协议透明」;与借轨函 #13(认证轨合作)是两条线,互不替代。
- 若原始 run 缺延迟数据且复跑成本高 → 降级:只提交 accuracy 侧不可行(LAFS 必须
  延迟)→ 如实记录「材料缺口,提交延后」,不造数。
