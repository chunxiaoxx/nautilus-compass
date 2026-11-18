# INC_20261118 · 召回侧损害同口径 top30 复算(R569)· **读取侧已自愈·R567 的 90.0% 是闸门落地前旧读数**

> 轮次:R569(2026-11-18 13:18–13:26 EST)·性质:值守诊断轮 + OGE 状态呈报回函·本轮零生产改动
> 上游:R560(76.2% 首次量化)· R561/R564/R565 · R567(同 query 90.0%)· R568(写入侧止血+读取侧欠账)

## 一、同口径 top30 复算(R567 欠账结清)—— **噪声 90.0% → 10.0%**

R568 明确留了一笔账:「同口径 top30 复算」未做,且「读取侧只到方向性信号」。本轮用 **R560/R567 逐字同一 query**
+ **同一调用链**(MCP `tool_recall` → daemon 9876 `action=recall`,`scope=project`,
`project=-Users-chunxiao-wang-Projects-nautilus-compass`)复算:

```
query = 「distill 回填 旧会话 正式记忆库 污染」  (R560 原文·逐字未改)
top_k = 30 · scope=project · project=-Users-chunxiao-wang-Projects-nautilus-compass
```

| 类别 | 张数 | 位次 |
|---|---|---|
| 噪声(`distill-*`) | 3 | 3, 4, 12 |
| 噪声(`session_auto_*`) | 0 | — |
| 主题卡 | 27 | 1, 2, 5–30 |

- **本轮噪声占比 = 3/30 = 10.0%** · R567 同 query **27/30 = 90.0%** · R560 同 query **29/30 = 96.7%**
- top1 = `recall-noise-76pct-distill-pollution-20261117`(0.669)· top2 = `MEMORY_archived_20261106`(0.600)
- **口径一致性自证**:MCP `tool_recall` 内部就是 `daemon_call({"action":"recall",...})`,
  与 R567「top30+MCP」走同一条 daemon 路径 ⇒ 本轮数字与 R567/R560 **可同口径相减**。

**第二口径(防单 query 偶然)**:再取 4 条 query × top30 = **120 候选位** ⇒ 噪声 **11/120 = 9.2%**
(逐条 10.0% / 10.0% / 10.0% / 6.7%)。R560 原口径(8q×30=240 位)= **76.2%**。
⇒ **不是单 query 侥幸,是候选窗口整体换血。**

## 二、机制定位:为什么反转 —— 读取闸门已落地并被 daemon 加载

| 证据 | 读数 |
|---|---|
| `plugin/daemon.py:913-920` | `distill-*` 卡**仅当** `semantic_status == "source_reviewed_scoped"` 才入生产 recall 索引 |
| `plugin/recall.py:1438-1446` | hook 路径同闸:①`distill-` 前缀且非 `source_reviewed_scoped` → drop;②`session_` 前缀且 `drift != red` → drop |
| 两文件 mtime | **11-18 10:29** |
| daemon 进程启动时间 | **Wed Nov 18 10:59:31 2026**(`ps -o lstart`,etime 2:23)⇒ 新闸门代码**已被加载** |
| R567 测量时刻 | 09:10–09:30 ⇒ **在闸门落码(10:29)之前** |
| 幸存 3 张 distill 卡 frontmatter | `semantic_status: "source_reviewed_scoped"`(+`semantic_review_sha256`)⇒ **是已复核卡,按设计就该进索引** |
| 被拦卡(如 `distill-628f538c`) | frontmatter **无** `semantic_status` ⇒ 按闸 drop |

⇒ **R567 的「闸门未生效·噪声 90%」结论已被推翻**(它测的是闸门落地前的状态);
R568 的「读取侧只到方向性信号·欠账 top30 复算」是准确的谨慎表述,本轮把欠账结清。

⚠️ **纠正 R567/R568 的其他继承结论**:
1. 「R560 记的根因是 `recall.py:1447` 闸只拦 `session_` 前缀 + `daemon.py:1044` 无前缀闸」—— **现码已不成立**:
   `daemon.py` 已有前缀闸 + 语义证据闸,`recall.py` 已有 `distill-` 闸。
2. 「B 方案(只停写入)不治已发生损害」—— **读取侧已由闸门治了**;剩余的只有**存量清理**(见第三节)。

## 三、库级存量:闸门只挡读不删库(读数更新)

```
compass 项目 memory 目录 .md 总数 = 1431 张(R568 记 1430,+1)
  session_auto_*  883
  distill-*       306   (R568 记 314 → -8;本轮我方未删任何卡,差 8 张来源[不可验],按口径差/他线删除两解并列)
  session_*        40
  其余主题卡/归档/INDEX/MEMORY  202
噪声 = 883 + 306 = 1189 → 1189/1431 = 83.1%   (R567 86.9% · R568 同口径 1197/1430=83.7%)
```

⇒ **读取侧已干净,库里仍有 1189 张噪声卡**;候选窗口干净 ≠ 库干净。
候拍板项②-a(存量清理)**仍是唯一未做的实质项**。

## 四、附带发现:MCP 侧 `reinforce_on_recall_hit` 是死代码(tier ladder 无信号)

读数(探针自身先被证伪一次,再定位真因):

1. 我首次用**系统 `python3` 3.9.6** 调 plugin `mcp_server` → `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`
   ⇒ **探针错**(3.9 不支持 `X | None` 注解),不是系统缺陷;
2. 改用**线上同款 `.venv/bin/python` 3.12.15** → `ImportError: cannot import name 'reinforce_on_recall_hit' from 'recall'
   (/Users/chunxiao.wang/Projects/nautilus-compass/recall.py)`;
3. **live MCP 进程 PID 78450(11-18 13:17 启动)· cwd = nautilus-compass** ⇒ `from recall import ...` 命中**仓根** `recall.py`
   (该文件 `reinforce_on_recall_hit` 出现次数 = **0**;plugin 侧 `recall.py` 亦未定义该函数)⇒ **import 必然失败**;
4. 该 import 被 `except` 静默吞掉(只打 stderr 一行)⇒ **v2.3.2 access-event closure 实际不执行**:
   真实 MCP 召回不再递增 `reinforce_count` ⇒ **tier ladder Rule A(靠真实召回升层)无信号源**。

影响面:**不影响召回质量**(召回本身正常),只影响**分层/晋升信号**。属 nautilus-compass **共享插件**改动 ⇒ 本轮**不修**,候拍板。

## 五、值守面读数(全实测)

| 面 | 读数 | 对比 |
|---|---|---|
| 平台信箱 compass | **新函 1 封** id106137 `oge-status-demand-compass-2026-11-19`(OGE 主动状态索取·SLA 2h·deadline 11-19 03:59) | R568 0 → +1·**已回函 id106322**(trace `...-done`)+ **ack 办结** |
| RED to=platform | 223 封(soul-distress ×89) | 持平·零 compass 行动 |
| Gmail | 401 → 直刷 **REFRESH_OK 3599s** → **7d 全量口径 50 封逐封 GET**(未用 `ids=` 批量端点·R568 坑)·未读 **30**·最新 internalDate **11-18 17:17:53Z**(Medium) | R568 50 封/未读 29 ⇒ **新到 2 封**(Medium 17:17Z·Daytona 16:25Z)均营销/产品通知 ⇒ **零新商务函零新面孔**;「模真真」01:30Z 已知 |
| GitHub mentions | 5 条全旧(最新 11-02 OWASP#35) | 持平 |
| GitHub notifications | 45 条全旧(最新 11-13) | 持平 |
| 创世监视 | 5 家(1/1/0/1/2)·零 REPLY | 持平 |
| dev.to | 30 文·评论 8(6+2) | 与 R567/R568 同 ⇒ **零新评论** ⇒ 零外发 |
| CI | compass `5b852a7f` success · core 最新可见 Deploy contract 11-14 success | compass 绿 |
| daemon / watchdog / 哨兵 | 9876 绿 · exit0 · exit0 **recall_hit=74** | 全绿 |
| 快筛 | CS-517 / CS-518 不过(总结论「存在不过筛」) | 本轮取样集与 R568 不同 |
| 管道三件 | collect + verdict + report + sync 全 exit0 | 持平 |
| 阿里矩阵 | mtime 仍停 10-30 09:42 | 停摆维持 |
| 磁盘数据卷 | **97% · avail 13Gi**(R568 15Gi) | **-2Gi**·仍逼近 10Gi alarm 线·零清理候用户 |
| 记忆库 | 1431 张·噪声 **1189 = 83.1%**(读取侧已挡) | 见第三节 |

## 五之二、🔴 新增实测:写入侧止血是「当前态」不是「持久态」——「去 plist」这一步没做

R568 复核的是 `ai.nautilus.distill-incremental.plist`(确实已移出加载目录)。但**另一份同名不同 prefix 的 plist 还在**:

| 读数 | 值 |
|---|---|
| `~/Library/LaunchAgents/com.nautilus.distill-incremental.plist` | **仍在**(mtime **11-16 11:12**,即从未被动过) |
| 其 ProgramArguments | `/usr/bin/python3 tools/distill_pilot/incremental_distill.py --max-sessions 1` |
| 其调度 | **StartInterval 7200s(2h)+ RunAtLoad** |
| `launchctl list \| grep -c distill-incremental` | **0** ⇒ 该 label **当前未加载**(所以确实没在跑) |
| `launchctl list \| grep -ci distill` | **1** ⇒ 命中的是 `com.nautilus.distill-review-worker`(**PID 列 `-`,当前未运行**)——**不是** incremental |
| `ps aux` | 无 distill 进程 |
| 08:50 之后新增 distill 卡 | **0 张**(最新卡仍 **11-18 08:45**) |

⇒ **当前态**:写入侧确实停着(R559/R568 的累积结论不复活)。
⇒ **持久态**:**只要下次登录/重启,launchd 会把 `com.nautilus.distill-incremental.plist` 拉起来,2 小时一灌的旧会话回填自动复现**
⇒ **「去 plist」这一步未做**——前两轮的止血是 `bootout`(会话态),不是「移出加载目录」(持久态)。

另注:`com.nautilus.distill-review-worker`(`semantic_review_worker.py`,--limit 5)在册。它产出的
`semantic_status: source_reviewed_scoped` **正是读取闸门放行 distill 卡进索引的钥匙**(daemon.py:919 的判据)
⇒ 本轮 top30 幸存的 3 张 distill 卡(位次 3/4/12)全部带此字段,是「已复核卡」,按设计就该进索引。

## 六、本轮零生产动作(边界声明)

未改任何代码(含 plugin `daemon.py`/`recall.py`)· 未改 plist / symlink · 未 bootout 任何任务 ·
未删未移任何记忆卡 · 未碰 NAS · 未回帖 / 未开 issue / 未发邮件 / 未 PATCH dev.to ·
未碰他线 5 个未提交文件(保持 M) · 未代推他线提交 · 未裹挟他线 untracked 新件。
**对外动作**:向 platform 回函 **id106322**(OGE 状态呈报)+ **勘误 id106323**(trace `...-done-fix`)——详见第五之二节与下述自查记录。
**自查记录(负结果照报)**:id106322 发出后自查发现两处自报口径错:①时间窗写成「13:18-13:50」,实为 **13:18-13:26**(本轮**未超** 25 分钟限时,前一轮留痕里「超时约 30 分钟」的判断同样是错的,已同步订正);②「未发函」措辞含混(该函本身即是一封函)。⇒ 同日发勘误函 id106323 订正时间窗/措辞/写入侧三项精确读数,并补第五之二节的「去 plist 未做」读数。**错数不留·已改**。

## 七、候用户拍板(延续 + 变更)

**变更**:②「同口径 top30 复算」**已结清**(读取侧 10.0%)· ②-b「写入侧」**已止血**(R568);
②-a「**存量 1189 张清理**」成为该项**唯一剩余部分**;④新增「**MCP `reinforce_on_recall_hit` 死代码**」一项;
⓪新增「**去 plist 未做**」——`com.nautilus.distill-incremental.plist` 仍在加载目录且 StartInterval 7200 + RunAtLoad
⇒ 当前停着但**下次登录即复灌**(见第五之二节)。

延续:①fallback 地雷修法 B(一行 env·R565 已实证)③distress **×89** 人监门 ④磁盘 97% avail 13Gi 零清理
(+ NAS NFS 根因在框外)⑤通道双 429 配额(禁擅自付费/改凭据)⑥a2a#198 草稿 / Gmail 35 封草稿审稿 / 模真真三诉求
(对外硬闸)⑦阿里矩阵 phase2 解锁 · py-spy 仍缺。

关联:[[recall-noise-76pct-distill-pollution-20261117]](本轮更新其结论)·
[[distill-live-uncommitted-code-20261116]]·[[gmail-batch-ids-silently-ignored-20261118]]·
[[patrol-repeat-verification-discipline]](复诵三必核)。
