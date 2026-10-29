# 阿里 CodeSense 部分交付 · 预注册判据档

> 预注册时戳: 2026-10-29 10:0x(+08:00) · 锚: 2026-10-30 18:00
> 裁定: 用户 10/29 拍板「部分交+诚实报数」——交过五条件的 N 道,缺口附判据锁坐标与修复排期
> 纪律: docs/soul/proposal_preregistered_recompute_20260914.md(报数纪律·soul approved)
> 本档只给判据与坐标,不给任何预期读数;N 与交付清单留白,由非实现者复算填。

## §1 判据(冻结·只许更严)

- 唯一口径: `nautilus-core/docs/feishu/质检方案_题目质量细节.md` 行525/527 程序性检查原文
- 五条件+区分度三指标,冻结文本已录入 `runtime/pipeline_state/criteria_lock.json`(八件判据实物 sha16·LF 口径)
- 开工前强制: `python3 ops/ali30q/verify_criteria_lock.py` → exit≠0 即判据漂移,拒判拒交
- 任何对本档判据的修改只能加严;放宽=交付作废

## §2 判定器与数据面坐标

- 判定器: `ops/ali30q/gate5.py`(v2·sha16 fcc310549ff390d1 在锁内)
  逐题判定+出局原因原文;分母固定 20;缺轮=该条件 None=不可判=不达标,U 显式留痕
- 数据面:
  - v5 items 树: `~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items`
  - compass 持久 scratch: `runtime/scratch_cs004b/codesense/items`
  - `/tmp/cs_decoy_20261027/codesense/items`(仅存,候迁持久)
- ⚠️ 数据面缩水实录[实测]: 10/29 快筛发现 /tmp 4 路已灭 3 路(cs_decoy_509/cs004b/cs514b),
  CS-509/CS-514B 判分读数下落候盘点(可能存于 v5 items 或 NAS 归档);三模块 SCRATCHES
  已收敛唯一源(collect_for_quickscreen)并指向持久路径,CS-004B 回收复测通过
- 批次纪律(F-009): 单批连跑禁跨夜拼;mtime 聚簇只取最新批;跨时段读数不混算

## §3 交付判定协议

- **N = 截止时刻 gate5 五条件+三指标全 PASS、且数据为截止前最新单批的题数**
- N = ________(留白·非实现者复算填)
- 交付清单(留白,逐题一行):

  | 题# | 机制ID(badpattern) | gate5判定时刻 | 批次号 | 环境标注 |
  |---|---|---|---|---|

- 每道交付题必附: UT 级明细九字段(criteria_v2_baseline.json「UT级明细字段清单」)
  + 三列并排(J1 甲方版 / J2 22580 加严线 / 梯度 pp),一版不得隐去
- 环境标注强制: 我方=Mac mini·32K 渠道·单批连跑;与甲方环境不可比,自测达标≠甲方环境达标

## §4 缺口披露格式(诚实报数)

- 未交题逐题: 缺哪几门 + gate5 出局原因原文 + 修复方向
  (③过简→加难 variant / ③过难→降难 / ⑤超档→UT 难度校准 / 缺轮→补跑)
- 修复排期由施工框(v5)回函确认后附入交付函;compass 不代诺工期
- 宁缺不硬凑(10/19 自举线定谳);空槽如实报空

## §5 复算安排(收工关)

- 非实现者复算: 新鲜会话,只信本档判据与下列自测命令,不信任何实现者自报
  1. `python3 ops/ali30q/verify_criteria_lock.py`
  2. `python3 ops/ali30q/collect_for_quickscreen.py --v5 --scratch > qs.json`
  3. `python3 ops/ali30q/gate5.py <item_dir>`(逐题,以交付清单所列坐标为准)
- 复算红灯先证伪自己探针,再质疑数据(10/9 纪律)

## §6 红线

不凑数 · 不放宽 · 无真值不自称达标 · 结论性陈述强制 [实测]/[推断]/[不可验] 分层
