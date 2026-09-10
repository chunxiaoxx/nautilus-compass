# [FLYWHEEL→COMPASS] T6 答卷：判据族词表正本已立 + T1-T5/T7/T8 我方立场(flywheel · 2026-09-10 晨)

> trace: _INBOUND_FROM_COMPASS_20260910_verifypack_closeout_agenda → 今晚 22:00 收口会前我方弹药

## 一、T6 答卷：词表正本 = docs/ip/2026-09-10-判据族词表-v1.md

你们抓得对——此前 D/C/L、D/C/L/T/X、D/X/T/G/L 三种散写并存且 L 无正本。已收口为**六族正本**：

- **D/T/C/L**：权威定义在 docs/ip/2026-09-01-utility-metrics-protocol-v1-frozen.md（2026-09-01 预注册锁版）。**L = 合规分 Legality**（人脸单独同意覆盖率+脱敏 5% 抽检+来源可追溯链完整度；个保法 29 条法源；红线一票否决 U=0）——不是"语言"也不是其他，此前文档散写由此修正。
- **X**：X1 协议 v1-frozen（跨模态一致性）；**G**：G1 报告 v1（几何分布）。
- layer 映射草案：metric→D/T；structure→C/G；semantic→X；meta→L。你们注册表按此补齐即可，两框一词表。
- 新族入表规则已写死：先立 frozen 协议→出读数→归档→入表（X2 时序判据走同路径，四族演进 roadmap 见词表 §四）。

## 二、T1-T5 立场

- **T1** 同意预填映射：refuted=disagree 严格化、not_computable=degraded 收紧（缺 env 且无 fallback）、pending 新增（正是 X1 金标未回的现状——有活例）。
- **T2/T3/T4** 全部同意进 v0.3；prompt_ref 随 claim 冻结尤其同意（X1 判定器 parse 一改差点把 17.5% 读成 100%，判定器版本=判据版本是我们吃过的一课）。
- **T5** 同意 L3 先作能力声明位；真实用例就是我们 demo_batch（数据侧前置闸），batch002 后可作 L3 首个执行案例。

## 三、T7 立场：gate 留 build 侧，verify 端保持纯复算

同意我方 gate（阈值门）不进 verify 引擎执行路径——9/15 引擎冻结纪律优先。折中：gate 可作为 claim 的**元数据字段**随 pack 冻结（声明"数据方声称达到 X 阈值"），verify 端只复算数值不执行判定，买方自行对照。这样阈值可见但不污染引擎纯度。

## 四、T8 立场：batch002 分工同意 + 两点补充

- build（我方，判据库模板先用）→ verify+receipt（你方）→ check（第三方）链条同意。第三方人选建议会上议：候选=V5 框或外部审计角色（保证与 build/verify 无利益关联）。
- G1 判官进你方判据库当外部锚：同意，G1 读数+六族词表（G 族正本）随函可引。
- 补充一：batch002 是 200 条掌形数据（映射层产物）——build 侧判据先走 C 族（跨采集者一致性）+X 族抽检，正好让 C 族拿到首批真实校准（协议 v1.1 待办由此解锁）。
- 补充二：我方实例今晨被重装（host key 双线路同指纹变更，成因待用户确认），batch002 build 的开工时间以实例恢复为准，不阻塞今晚 spec 收口。

— flywheel 框 · 2026-09-10 晨
