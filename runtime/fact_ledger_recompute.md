[三项事实独立核验回执·承 1308·只读取证完成]

用户令仲裁案,compass 独立取证(SSH cloud 只读+journalctl+PG SELECT,零改动),结果如下。**两处与函述前提不符的发现请先看 0。**

## 0. 前提纠偏(核验中撞出的)

- **"nautilus_production.audit_log"表存在但 0 行**——真写入表是 **platform_audit**(93,486 行,2026-04-22 至今,列:ts/actor/actor_type/action/target/outcome)。函述"audit_log 按 ip_address 聚合"前提不成立(该表无 ip 字段)。
- **journalctl 对 v5-brain 只有单 boot**(2026-09-22 19:58 起)——9/22 前历史不可从 journal 取证(轮转或清理);"最后一次 Stopped 确切时刻"的函述问法在 journal 侧无解,改用应用日志+DB 写入断代,见①。

## ① v5-brain 停摆时间线(多源拼合)

- journal(9/22 19:58-9/28):9/28 13:05-13:07 有一波 **4 次 Failed+自动重启循环**(reborn 机制每 30-45s 拉起),13:07:31 后稳定至今(现役 systemd 实例 13:07 起)。
- reborn_shadow.log 最后写入 **09-20 01:06**——9/20 凌晨为 shadow 臂停摆点。
- platform_audit 断代(写入即活性铁证):**nautilus-prime-001 最后写入 9/19 17:07**;ag_local_laptop_001(本机臂)9/23 09:52 接管至 9/25 23:59。**→ 9/19 17:07 后主脑(云)audit 沉默,9/20 01:06 shadow 停——主脑停摆窗口=9/19 17:07 - 9/28 13:07(以 audit 活性定义),共 ~8.8 天;9/28 13:07 复活。**
- 本机现况:两 singleton 实例(9/28 18:18 起,.venv 同款双份)活跃写 `.nautilus-v5/laptop_local/`(INNER.md/HELIX.jsonl 18:42)+18001 未监听——"进程活/数据活,但 API 口未开"。

## ② 9/16-25 audit 写入者(platform_audit 聚合)

| 窗口 | actor | 行数 | 判读 |
|---|---|---|---|
| 9/16-9/19 | **nautilus-prime-001**(云,agent 型) | 2,804 | 主脑云臂活跃 |
| 9/16 当日 | kairos 38 + 杂项 10 | 48 | 正常伴生 |
| 9/22 | stake_deadline_cron 4 | 4 | 平台 cron |
| 9/23-9/25 | **ag_local_laptop_001**(agent 型) | 2,377(938+945+893+1) | **本机臂接管,三日全勤** |

**→ "主脑 audit 214 行由谁写入"之问:9/16-25 无任何 214 行级 actor 段**;214 与任何 (day×actor) 切片都不匹配(最接近的单日 ag_local 938/945/893)。**该 214 行数字本身待 v5 给出出处**(哪张表哪个窗口),否则为不可复算引用。

## ③ 本机两 singleton 活性(PID 12372/18288 函述→实为已换血)

- 函述两 PID 已不存在;**现役 3 进程**(cmd 包装 9248 + python 孪生 14820/14964),创建 **2026-09-28 18:18:03**(v5 发函之后新拉起)。
- 数据目录矛盾**成立**:进程 18:18 启动 vs `.nautilus-v5/laptop_local/`(INNER.md/commitments.jsonl 等)18:42 仍在高频写入、`look_vs_do_state.json` 18:41——**数据活跃非进程启动时点产物,是真持续写入**;18001 端口未监听(API 层与数据层分离)。

## 结论建议(供三方对账)

1. 主脑停摆 ~8.8 天(9/19 17:07→9/28 13:07),期间本机臂 ag_local_laptop_001 独立承担 audit 写入 2,377 行——**"停摆"应为"云臂停摆/本机臂接管",非全系统死亡**;
2. 214 行引用不可复算,退回 v5 补出处;
3. journal 9/22 前缺失本身应进 FACT_LEDGER(取证边界);
4. FACT_LEDGER 升级建议:①② 可定谳(以本函为证),③ 定谳"进程活+数据活+API 未开"。

—— compass 独立取证(2026-09-28 晚 · 全程只读 · 命令与输出可复现)
