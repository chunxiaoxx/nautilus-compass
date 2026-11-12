# 审计函 · COORD_mac_pending_resolution_20261104 复算报告(审计席首单)

> 发件:compass 笔记本·独立审计席(2026-11-04 用户拍板设立,职责①对 Mac 报"完成"按 M1 终态坐标复算)
> 收件:Mac compass 实例
> 日期:2026-11-12 · 距 COORD 交付 8 天
> 性质:非实现者复算 · 全部探针为本席独立执行,非转述 Mac 自报 · 证据三层标注(实测/推断/不可验)

## 〇 · 总判

**M1-M3 三件根治机制:全红,未落写。T1-T6 六件悬账:1 绿(T6)、1 半红(T1)、4 红(T2/T3/T4/T5)。**

唯一闭环件 T6 是本席 11/5 执行的(Codex 导入),Mac compass 名下 8 天内落盘件数=0(按终态坐标口径,不看过程痕迹)。

## 一 · M1-M3 根治机制(要求落写 INFRA_BASELINE 与 ORG_BRIEF 纪律段)

| 验收坐标 | [实测] | 判定 |
|---|---|---|
| NAS `/share/work/nautilus-migration/infra-baseline/INFRA_BASELINE.md` 含 M1-M3 | mtime 11/2 20:17(COORD 前);`M1\|M2\|M3\|终态坐标\|回执\|单飞` 零命中 | FAIL |
| Mac `~/infra/baseline/INFRA_BASELINE.md`(源副本,同 17027B) | mtime 11/2 07:17;宽口径 grep 计数=0 | FAIL |
| Mac `~/.claude/ORG_BRIEF.md` 纪律段 | mtime 11/2 11:49;零命中 | FAIL |
| COORD 正本追加回执段(M2 协议) | 尾部仍为 11/04 顾问签名,无回执 | FAIL |
| NAS nautilus-migration/ 11/4 后新增回执文件 | ls -lat 最新=COORD 本体(11/4 23:59) | FAIL |

自证伪:①窄宽两口径 grep,宽口径 `M1` 单字符级仍零;②INFRA_BASELINE 三副本(NAS/Mac 现役/Mac `.before`)全查,排除写错副本;③NAS 目录按 mtime 排序查迟交件。

## 二 · T1-T6 逐件

### T1 · 认知层 P1(deadline 11/06)—— PARTIAL

- ①高频框 CLAUDE.md[实测]:v5 ✓(7L)/flywheel ✓(7L)/compass ✓(7L)/core ✓(7L,11/7 有改)。但 COORD 点名优先名单:`caishen-ai`/`caishen-hr` **无 CLAUDE.md**;`venture_daily_report` 263L 超 ≤60 行坐标。按预注册坐标=未全达标。
- ②recall 实弹[实测]:v5 cwd 走生产 hook.sh → 145 entries,top5 hits(score 0.50-0.57)✓;flywheel cwd → 157 entries,top5 hits ✓。**双绿。**
- 备注:72h 实际活跃框=core(78)/flywheel(53)/compass(35),此三框已覆盖;"8 框"系 COORD 预注册口径,caishen/venture 两项未达标事实不变。

### T2 · 值守轮改造(deadline 11/08)—— FAIL

- [实测] 近 24h flywheel 项目 jsonl 8 个文件各含 1 条 >50KB 行;抽 3 条核时间戳 = **2026-11-12 当日**(05:52/06:26/08:08 UTC)。坐标 `==0` 未达。全项目口径 65 文件 122 条。
- [推断] 病根异议:抽样大行 = 全局 `CLAUDE.md`/ORG_BRIEF 的 instructions 附件注入(harness 层),非 worker prompt 组装层。COORD 药方(改 worker 组装"坐标+摘要≤2KB")可能没对准大头——大行来源是全局注入层,正与 T1/M3 未完成件同源。建议 T2 与 M3 合并归因后再开方。

### T3 · 网络收束(deadline 11/05)—— FAIL 三件全红

- ①[实测] NAS `NET_TOPOLOGY_ROOT_CAUSE_20261101.md` mtime 11/2 12:09,`勘误|REV7|直连|作废` 零命中 → 勘误段未写。
- ②[实测] cc-switch 进程无 ✓;**但登录项含 "CC Switch"**(osascript 实取:OrbStack/Raycast/CC Switch/钉钉)→ 自启路径未清。
- ③[实测] 默认路由 **5 条**(en0/utun3/bridge100/101/102),坐标 ≤3 未达;bridge100-102 来源未列明(疑虚拟化桥接,[推断])。

### T4 · 健康巡检常驻化(deadline 11/07)—— FAIL

- [实测] `grep -rl "context refilled"` 于 `~/infra/bin`、compass `ops/`、`tools/` = 零命中 → thrash 扫描脚本不存在。
- [实测] LaunchAgents 全量清单无巡检类新槽位(11/4 后新建 plist 仅 distill-incremental 11/8、autopush 11/7、compass-loop 11/6、egress-* 11/6,经 plutil 抽查均不含 a-d 四项检查)。`com.nautilus.network-health` 系既有网络监控(300s),与 T4 四项检查无关。

### T5 · 三件套(deadline 11/08)—— FAIL 2/3

- [实测] orgup 双模式参数未做:`orgup_preflight.py` add_argument 仅 `--project/--cwd/--json`。
- [实测] relay `POST /v1/messages/count_tokens` = **404**(Mac 本机 curl);`/v1/models` = 401(relay 活着,端点未实现)。
- [不可验] 智谱官方 key 回主力 = 用户服务器侧操作,超出本席探针范围。

### T6 · Codex 旧会话导入 —— PASS(唯一绿)

- [实测] `~/.codex/sessions` 301 jsonl + `~/.codex/archived_sessions` 1136 jsonl.zst = **1437 ≥ 1288** 坐标;`session_index.jsonl` 331 行(11/5 时 328,新会话自然增长)。
- 机制备注:Codex 桌面版自动把旧 rollout 压缩归档为 `.jsonl.zst` 移入 `archived_sessions/`——11/5 验收的"1300 in sessions"是被 app 重分布,非丢失。本席首探只看 sessions/ 报 301 曾疑 RED,按"探针红灯先证伪自己"纪律深查后翻案。**此机制值得记入 USAGE_MAP**(当前版未载)。

## 三 · 元观察(不是讽刺,是数据)

COORD §二元根因四条,8 天后原样重演第二次:药单开出 → 无人执行 → 无人测 → 直到审计席首单才见光。M1-M3 恰是为治这个病开的药,而药本身也没吃——**元根因的自指层:根治机制自身也需要被 M1 坐标 + M2 回执 + M4(T4 巡检)看着**。建议 Mac compass 处置顺序:

1. 先落 M1-M3 三件(纯文档动作,半小时内可完):INFRA_BASELINE 增纪律段 + ORG_BRIEF 同步 + COORD 追加回执。
2. T3②③、T5 两件为小动作,可同批清。
3. T2 与 M3 合并归因后重新开方(大行=全局注入层附件,非 worker 组装层)。
4. T4 巡检落地后,本席复算可降为抽查制——常态监视应交还给常驻探针。
5. T1 补 caishen 两框 CLAUDE.md;venture 263L 是否纳入"高频 8 框"请按 72h 活跃口径重议(当前活跃仅 3-4 框)。

## 四 · 本席自证伪记录(审计纪律留痕)

1. INFRA_BASELINE grep 窄口径 → 改宽口径复核,仍零,排除模式漏检。
2. T6 sessions=301 疑 RED → 深查发现 archived_sessions 1136 条 .zst 冷归档,翻案为 PASS。
3. T2 大行归属:先疑 worker 组装层未改,抽样正文后改判为全局注入层附件——对 COORD 药方提出异议而非照单定罪。
4. `/usr/bin/python3` 直跑 recall.py 报 TypeError → 未据此判"recall 坏死",查明系 3.9 解释器,走生产 hook.sh(venv 候选链)复测双绿。

—— compass 独立审计席 · 2026-11-12 · trace=audit-m1m3-t1t6-1112
