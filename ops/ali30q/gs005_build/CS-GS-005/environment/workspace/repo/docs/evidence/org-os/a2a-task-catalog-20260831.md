# A2A 可外包任务类型目录 v0(2026-08-31 · 用户拍板"回执到了直接用")

> 用途:compass/flywheel 常驻件注册回函(id 109/110)一到,平台按本目录投第一批组织级 a2a 单。
> 依据:生产表 `a2a_delegations` 实测——296 条存量里 258 expired / 28 verified / **近 30 天新单 0**;verified 样例全是旧 kairos 生态互检单(peer check),非组织级任务。**反面教材 = 自由文本无验收判据 = expired 剧场。**
> 机制:全部复用现有表结构与流转(open→accepted→delivered→verified · task_text + metadata jsonb + nau_offered + deadline + delivery_payload + verification_note),**不新增机制**。

## 每单强制五件套(缺一不发)

1. **类型标签**:task_text 开头 `[C1]`/`[F2]`;metadata.task_type 同步
2. **验收判据**:verified 的机械标准(探针/SQL/比对式,拒绝"看起来不错")
3. **交付格式**:delivery_payload 结构(逐字段写明)
4. **deadline + 预算**:SLA 默认 2h 起步按活计;NAU cap 对齐协议 v1 花销纪律
5. **消费者**:结果进哪个决策/哪份日报(§⓪-E:无消费者不发单)

## C 类 · compass daemon(读数 / 审计 / 记忆)

| # | 任务 | 验收判据(verified 标准) | 交付格式 | 消费者 |
|---|---|---|---|---|
| C1 | 记分牌独立读数 | 5 数字(income/verdict/自治率/settle/capability)各带 SQL 出处+与上轮差值;与平台自报不符时逐项亮牌 | {metric, value, sql, prev, delta}[] | 平台日报 + convergence |
| C2 | 函件对账 | mailbox DB vs loop_state.json 逐封比对,缺口清单含函 id;抽样 has_reply 复核 | {letter_id, loop_claim, db_truth, gap}[] | compass 审计章程项 A(9/1 首单已预演) |
| C3 | 日报体检 | 各节非空壳:字数门槛+关键数字存在性检查 | {section, ok, reason}[] | 审计章程项 B |
| C4 | 台账消费计数核对 | 台账行 vs 实际引用(代码/函件/日报)交叉,30 天零消费者名单 | {asset, last_consumer, days_idle}[] | §⓪-E 退役红灯 |
| C5 | evidence 对账 | verdict POST 记录 vs 云 DB 行,g2b1-exec-* join 规约逐条验 | {exec_id, posted, db_row, match}[] | 转移线④执法 |
| C6 | 疑点专案 | 限定只读;结论含证据链+复现命令(样例:notified_at 之谜已在产) | 审计小报节 | 审计章程 |

## F 类 · flywheel daemon(数据管道 / QC)

| # | 任务 | 验收判据 | 交付格式 | 消费者 |
|---|---|---|---|---|
| F1 | QC 初筛判读 | qc_gate_v0 口径;抽样 10 行与人工 QC 零分歧(漏判=0 误伤=0) | {row_id, verdict, confidence}[] | 垂域交付线 QC 降本试点 |
| F2 | 附件 PII 扫描 | 82 违规文件口径复跑;新扫描报告逐文件列违规类型+位置 | {file, pii_type, location}[] | 附件包定位阻塞(22:00 PII 活直投) |
| F3 | 出题候选初筛 | 双臂筛口径:minimax 全 0 × deepseek>0 交集;逐题附 verifier 思路列 | {task_uid, arm_a, arm_b, verifier_idea}[] | 12 题 A 候选加工 |
| F4 | 燃料池盘点 | fuel_pool 目录 vs 台账逐条对账;不一致清单 | {pool_item, ledger, gap}[] | 燃料台账 |

## P 类 · 通用监控(平台发起,任一 daemon 可接)

| # | 任务 | 验收判据 | 消费者 |
|---|---|---|---|
| P1 | endpoint 探活 | 指定端点清单 curl 实测(HTTP 码+延迟),非"应该活着" | supervisor |
| P2 | timer 心跳 | systemd timer 最近触发时刻 vs 间隔,滞后即亮牌 | supervisor |
| P3 | 部署后验证 | 云端 commit hash 读回 = 预期 + 记分牌部署前后对照 | DEPLOY_DISCIPLINE |

## 禁区(永不外包,随单重申)

- 方向生杀 / 预拍 → 用户专属
- verdict 终裁 → 双门独立复核(平台+soul),外包只做初筛
- 发函决策 / 状态升格 → L3
- 生产配置变更 / 部署 → DEPLOY_DISCIPLINE,禁 VM 直改
- 业务内容定稿 → 专家亲笔红线

## 首批试点投单计划(回函到达后)

| 时序 | 单 | 收件 daemon | 备注 |
|---|---|---|---|
| 9/1 compass 回函即投 | C2 函件对账 | compass daemon(注册后 agent_id) | 与其审计首单同源,一鱼两吃=机制自测 |
| 9/1 flywheel 回函即投 | F2 PII 扫描 | flywheel daemon | 其 22:00 本有 PII 活,改走 a2a 通道 |
| 9/7 检验点 | — | — | a2a 消费计数进台账;零消费=目录降档 |

## 旧单切割

存量 296 条(kairos/hr-agent-web 生态)标 `legacy`,不清理不续投;新单一律带本目录类型标签,verified 判据按五件套。两套口径在 metadata.era = `legacy` / `org-v0` 区分。
