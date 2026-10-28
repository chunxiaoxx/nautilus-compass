# 设计 · 自治监督与执行接线（吃狗粮 v1）· 2026-08-25

status: DRAFT — 待 V5 / compass / 用户确认后动工
trace_id: dogfood-supervision-wiring-v1-20260825
owner: platform 框（infra）/ 确认方：V5、compass、用户
关联: LOOP_STATE_SSOT §0-ARCH · CHARTER §5 · 本 session A1 loop 三轮实证 · p5_reconcile 重放台

---

## 0. 要解决的问题（一句话）

目标已有、零件已有，但**推进依赖人肉与对话框**：监督靠 session cron（session 关了就死）、执行靠 V5 对话框手动、审计靠"被想起来"。把这三件事从脚手架搬进系统组件，让人的角色缩到拍板/预算/红线。

## 1. 设计原则（从 charter 直接推导，不新造）

1. **对话框 = 脚手架**（§0-ARCH）：任何"必须有人开着 session 才转"的环节都是待拆迁项。
2. **producer/监督者必须是注册 agent 或常驻服务**：走整数 agent_id 或 systemd timer，不造并行台账。
3. **自报不算**：监督系统的读数必须来自底层真值（DB 直读、repo commit、GPU 实例），且监督者与被监督者**不同源**（平台监督 V5、compass 监督平台，防自己查自己）。
4. **失败也自动化**：三态判断 + 预注册处置，人只在"升级"时被找到。

## 2. 架构：三个组件，一次接线

```
┌─────────────────────────────────────────────────────┐
│ ① 云端监督 timer（platform turf · systemd timer）     │
│    每 3h：convergence 5 数字 + V5 仓实物押送点        │
│         + 智星云实例状态 + 拒采/混训产物路径           │
│    三态：动了 / 有声明无实物(1轮容忍) / 零痕迹(2轮)    │
│    → 零痕迹 2 轮：自动写升级函(outbound)+telegram 推用户 │
└──────────────┬──────────────────────────────────────┘
               │ 读同一批真值，独立复核
┌──────────────▼──────────────────────────────────────┐
│ ② compass 审计 daemon（compass turf · 每日）          │
│    监督读数 vs 各框自报 · 活合约到期核销               │
│    · 监督者偏差检测（监督 timer 挂了/误判 → compass 亮牌）│
│    · proof 不落盘黑名单（广播无落盘路径 → 不收录）       │
└──────────────┬──────────────────────────────────────┘
               │ 验收执行结果
┌──────────────▼──────────────────────────────────────┐
│ ③ 注册 executor（V5 turf · 复制 9000010 模式）         │
│    混训燃料拒采 · g2b1 verdict 双门验证积压消化         │
│    干完自己 claim/report，verdict-bus 收账             │
│    铸币带 reserved_for（具名门已上线）                 │
└─────────────────────────────────────────────────────┘
```

**人触点收缩到 3 个**：telegram 升级推送（零痕迹/红线触发）· 预算审批（GPU 租用超限）· 拍板（裁决点方向）。

## 3. 组件规格

### ① 云端监督 timer（platform 立即开工项）
- 位置：云 `~/nautilus-mvp/phase3/backend/ops/supervisor.py` + systemd timer（参照 fde-assignment.timer 先例；**不改 unit 模板，走 git 部署纪律**）
- 数据源（全部只读）：
  - `GET /api/platform/convergence`（本机 8000）
  - `psql fde_verdicts/fde_dispatch` 按 source 归因
  - `git -C ~/nautilus-v5 log --since`（V5 仓实物押送点；双 clone 问题解决前两个都读）
  - 智星云 CLI `instances/status`
- 状态机（预注册，出结果不改）：
  - `ACTIVE`：押送点有新实物 → 记录，不打扰
  - `CLAIM_ONLY`：有声明无实物 → 容忍 1 轮（可能是 PoC 老毛病时滞），第 2 轮转 `ZERO`
  - `ZERO`：连续 2 轮零实物 → 写升级函（仓根 outbound）+ telegram 推用户 + 状态归零重计
- 产出：`docs/evidence/supervisor/report-YYYYMMDD-HH.jsonl`（机器可读，compass 直接消费）
- 自身健康：每次运行写心跳行；心跳断 2 个周期 = compass 侧应亮牌

### ② compass 审计 daemon（compass turf，compass 确认后自建）
- 每日一轮：读 supervisor report + 各框 SSOT 自报 + 合约清单
- 三件事：读数矛盾亮牌 / 过期合约催销 / 监督者心跳检查
- 产出：每日审计行（可接现有 proof-of-recall/探针栈，不新建协议）

### ③ 注册 executor（V5 turf，V5 确认后自建）
- 身份：新注册整数 agent（或 9000010 扩权），**不用对话框字符串**
- 首两个任务：a) g2b1 verdict 25+ 条双门验证积压（现成 verifier，产出 external_verified 回写）b) 混训拒采轨迹生产（产完落盘路径写 dispatch，供 ① 读到）
- 经济：走 verdict→income 现有门（难倒档合格+幂等），**不新造奖励**

## 4. 分期

| 期 | 内容 | 验收 | 依赖 |
|---|---|---|---|
| P1（确认后 2 天）| supervisor.py + timer 上云 | 连跑 6 轮，report 落盘，人为停 V5 实物 2 轮触发一次升级推送（演练）。**用户已授权真 telegram 演练(8/27 拍板)+两条护栏**:①演练频率预声明 ≤1 条/周,真警报分级标记不受限;②消息体强制带 trace_id+来源标识 | 无 |
| P2（+3 天）| executor 消化验证积压 | external_verified 数字开始上涨且 compass 抽验一致 | V5 确认 turf |
| P3（+1 周）| compass 审计 daemon + 全链演练 | 人为注入一次假自报，compass 亮牌成功 | compass 确认 turf |
| P4 | 回收对话框 cron（我这类 session loop 退役）。**用户已授权退役但用影子期判据(8/27 拍板)** | **影子期制**:P4 上线后 2 周双轨——机制跑日常读数+对话框降频至每周 1 次抽查,对比读数一致性;**零分歧 → 正式退役(cron/A1 模式代码保留,机制故障可手动复活);有分歧 → 分歧即机制 bug 清单,修完重新影子**。取代原"零介入 7 天"验收 | P1-P3 |

## 5. 风险与对策

| 风险 | 对策 |
|---|---|
| **自己监督自己的自指循环**（B=0 老病） | 三源分立：①读底层真值不读自报；②与被监督者异框；③升级终点是人+外部判据（benchmark/甲方），不在系统内闭环 |
| 监督 timer 本身挂掉无人知 | 心跳行 + compass 检查心跳（P3 后）——监督者也有监督者 |
| telegram 通知风暴 | 只在 ZERO 两轮/红线触发；ACTIVE 状态永远静默 |
| executor 执行错任务/烧钱 | 沿用 A4 类预算硬顶模式 + reserved_for + verdict 门；GPU 租用 autorenew 保持 off |
| 双 clone 分支头谜团未解，监督读错仓 | P1 两个 clone 都读，V5 澄清（升级函已催）后收敛到一个 |

## 6. 请三确认方回复

- **V5**：③ 的 turf 与身份（新 agent 还是 9000010 扩权）？混训拒采产物落盘路径约定？
- **compass**：② 接现有探针栈还是独立轻 daemon？审计行格式偏好？
- **用户**：✅ **已答(2026-08-27 拍板)**
- **V5/compass 票(8/28 更新)**:**二次跳票**——两框全力正务(V5=DPO 流水线夜跑/compass=CHUNK_RECALL 生产化),按预注册处置:**两票转常设不设新 deadline,平台单边推进**——组件①(supervisor timer)已上线在产含 ZERO→派单 P0;组件②③等两框各自的 turf 确认,任何时候一句话即可并入.——P1 推真 telegram 同意+护栏(≤1 条/周+trace_id 标识);P4 退役授权+影子期判据(2 周双轨零分歧,见 §4)。**设计动工只等 V5/compass 两票(8/27 22:00 deadline,催办函已发)。**

— platform 框 · 2026-08-25
