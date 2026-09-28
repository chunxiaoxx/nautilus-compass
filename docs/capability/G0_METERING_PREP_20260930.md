# G0 盲测计量预备(2026-09-30 凌晨 · 10/2 硬节点前置)

> 我方角色(正档任务表):zenmind 执行盲测,compass 计量单全程记录。
> 通道:POST /api/platform/org/assay/meter(1362 用法已核),每测一条挂一单。

## 一、G0 四判据的计量单映射(每判据每次测量→一单)

| 判据 | target_object | reading_hash 内容 | 预期单量 |
|---|---|---|---|
| J1 记忆可感知率 | qida-G0-j1-perception | 正确归因数/20+臂映射版本 | 每臂批次 1 单 |
| J2 价值差(推荐意愿) | qida-G0-j2-recommend | A/B 各自愿数+差值 | D14 1 单 |
| J3 自发提及率 | qida-G0-j3-mention | 提及数/日次+正则版本 | 每日访谈 1 单 |
| J4 抗新奇衰减 | qida-G0-j4-return | 第 7 天回访数+双臂差 | 第 7 天 1 单 |

judge_version=qida-ledger-prereg(2cee081)——判据版本锚=预注册 commit。

## 二、考官面三注记的落地(评审 1319 的执行件)

- 注记①(小 n):J1/J2 的计量单 reading_hash 附二项 CI(报告口径);
- 注记③(端点降级):本通道即 1362 端点,已上线=降级预案撤销;
- 抽检:20 码的臂分配(arms.ts fail-closed)开测前快照哈希入档(判据冻结物证)。

## 三、时间线检查单(10/2 开测日)

- [ ] 开测前夜:arms.ts 快照哈希+20 码分配记录入档
- [ ] 开测日 00:00(startDate 锚):首条 J3 日访谈计量单
- [ ] 每日:J3 单+episodes 日志抽查(自动判读路径)
- [ ] D14:J1/J2 单+揭盲脚本运行(阶段盲录不破盲)
- [ ] 第 7 天:J4 单
- [ ] 全部读数汇总:四判据对照预注册判定(任一不达复盘不改判据)

## 四、分工确认

- zenmind:测量执行+每测挂单(它已认领 Assay 计量首消费)
- compass:单据抽验(考官面)+reading_hash 口径核对+四判据终判呈报
- platform:通道与回执(GET receipt/{id} 客户可回读=发票雏形)
