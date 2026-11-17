# 🔴 distill「freeze」被证伪·旧会话回填持续灌入正式记忆库（2026-11-17 R559 值守轮）

> 承接卡：[`DISTILL_BACKFILL_STILL_LIVE_20261117.md`](DISTILL_BACKFILL_STILL_LIVE_20261117.md)（R558）→ [`DISTILL_LIVE_BACKFILL_RISK_20261116.md`](DISTILL_LIVE_BACKFILL_RISK_20261116.md)（R557 追记）。
> 本卡只记 **R558 之后** 的新增实测事实与结论增量。标注 [实测]/[推断]。
> **本轮零生产动作**：未 bootout/stop launchd、未改 plist、未改他线未提交文件、未推他线提交。

## 0. 一句话

**他线的 freeze 提交 `dd821259` 对「选择面」完全无效——本轮实测在其落地后 10 小时内又发 5 张 28 天前旧会话卡进正式记忆库；且脚本无任何配置级刹车参数，刹车只能改代码或停任务。**

## 1. 证伪：freeze 提交后仍持续发布旧会话[实测]

他线提交 `dd821259 fix(distill): freeze evidence-bound incremental pipeline`（2026-11-17 02:09:22 EST）。

R558 记录 freeze 后 02:11 仍发 1 张（`ff33617d`）。**本轮实测其后 10 小时内又发 5 张**：

| 卡（正式记忆库） | 落盘时刻 | 源会话 jsonl mtime（`incremental_stats.jsonl` `source_mtime_ns`） | 距今 |
|---|---|---|---|
| `distill-6e9efa34-…` | 11-17 04:14 | 2026-10-19 23:4x EDT | **28 天** |
| `distill-0fe9543a-…` | 11-17 06:16 | 2026-10-19 23:4x EDT | **28 天** |
| `distill-1ec53149-…` | 11-17 08:18 | 2026-10-19 23:45 EDT | **28 天** |
| `distill-a99dc9f2-…` | 11-17 10:21 | 2026-10-19 23:43 EDT | **28 天** |
| `distill-3f582dab-…` | 11-17 12:23 | 2026-10-19 23:40 EDT | **28 天** |

- 落盘时刻间隔 **≈2h**，与 plist `StartInterval 7200`（每次 `--max-sessions 1`）完全吻合 ⇒ 逐轮 `launchd` 触发，非一次性残留。
- 线上日志 `runtime/scratch_distill_pilot_20261104/incremental.log`（mtime **11-17 12:23**）末行 `[incr] 3f582dab published`。
- ⇒ **结论：freeze 提交对「哪些会话进候选」这一层没有任何约束力**，R558 的「B1 选择面未收口」由「待验证」升级为 **已证伪**。

## 2. 根因[实测·读线上代码]

线上执行路径 = 工作区 `tools/distill_pilot/incremental_distill.py`（plist `ProgramArguments` 直指，**HEAD=dd821259，该文件本身已提交**）。

`collect_pending()`（`incremental_distill.py:147-165`）排除条件仅 4 条：

```
stat.st_size < MIN_SIZE                      → 小文件跳过
now - stat.st_mtime < WRITING_WINDOW         → 正在写入跳过
PATROL_RE.search(light_first_user(path))     → 命中排除
source_sha256 命中 且 缓存/发布有效           → 已处理跳过
```

**无任何时间下界**（不排除 >7d 旧会话）。语义由「mtime 水位」换成「内容哈希」是**证据绑定**的改进（B2 已收口：回执校验 `publication_valid` / `cache_valid` / `publish_revision`），但**存量旧会话仍被逐张写进正式记忆库**。

**并且没有配置级刹车**：`argparse` 实测可用参数仅 `--dry-run / --force / --runtime / --bucket / --memory-dir / --only / --max-sessions` —— **无 `--max-age` / `--since` 类参数** ⇒ 除非改代码或停任务，**无法从 plist 侧限流**。

## 3. 污染量化[实测]

| 指标 | 实测值 | 来源 |
|---|---|---|
| 桶内会话 jsonl 总数 | **2043** | `~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/*.jsonl` |
| 其中 >7d | **1958（95.8%）** | `mtime` 实测 |
| `incremental_stats.jsonl` 总行 / published / review | 351 / **270** / 78 | 逐行解析 |
| **published 中源会话 >7d 的比例** | **270 / 270 = 100%** | `source_mtime_ns` 实测 |
| 已发布卡来源日期分布（前 4） | 10-20×162、10-27×25、10-21×19、11-01×12 | 同上 |
| 正式记忆库 distill 卡总数 | **1414**（含 `MEMORY.md` 计 1415） | `ls ~/.claude/.../memory/*.md` |
| 余量（>7d 存量 − 已发布） | **≈1688** | 1958 − 270 |
| 按 12 张/天 的排空工期 | **≈141 天** | 1 张 / 2h |

⇒ **正式记忆库当前由本管线写入的 270 张卡，100% 来自 >7d 旧会话**；若不收口，后续 ≈141 天内将以约 12 张/天 的速率持续灌入。

## 4. 「线上跑未提交代码」仍成立[实测]

`incremental_distill.py:21-24` live import 链：

```
from anchor_check import …
from compress_arm import compress_session      ← 已随 dd821259 提交
from extract_sample import extract_file         ← 未提交 (+188)
from publish_to_memory import MEMORY_DIR, …     ← 未提交 (+243，正式记忆库写入方)
```

工作区未提交（本轮**未触碰**）：`extract_sample.py` +188、`publish_to_memory.py` +243、`p3_delta.py` +57、`fuel_intake.py` +5（`git diff --stat` 实测）。

## 5. 本轮零动作声明

| 动作 | 本轮 | 理由 |
|---|---|---|
| `launchctl bootout` / 停 distill | **未做** | 三选项候用户拍板（R558 §7 已列）；停生产任务属他线状态变更 |
| 改 plist / 改 `collect_pending` 加时间下界 | **未做** | 属改他线代码，需先定「旧存量如何处置」再动 |
| `git add/commit/checkout` 他线 4 文件 | **未做** | 保持 ` M` 原样，不裹挟落账 |
| `push` 他线提交 | **未做** | 本地 HEAD=origin/main 已零领先（R558 后已推），无待推项 |

## 6. 候用户拍板：一个最小动作（可逆）+ 三个完整选项

**最小刹车（推荐先做，30 秒可逆）**

```bash
# 停：回填即刻停止（launchd 装载态卸载）
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.nautilus.distill-incremental.plist
# 恢复（若后续决定继续跑）
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.nautilus.distill-incremental.plist
```

**三个完整收口选项**（R558 §7 沿用，本轮补上量化依据）

1. **选面收口**：给 `collect_pending()` 加时间下界（如 `now - mtime <= 7d`），把 1958 个旧会话存量挡在正式库之外；存量另置「归档区」而非正式库。**代价**：需改他线已提交的 `incremental_distill.py`（+1 行判断），需与该线施工方协调（其工作区另有 4 个未提交文件）。
2. **未提交收口**：`publish_to_memory.py` / `extract_sample.py` / `p3_delta.py` 落账，或 launchd 改指 HEAD 固定副本（`git worktree` / release 目录），使「线上跑什么」可审计。
3. **动作收口**：若不再需要该管线 → `launchctl bootout`（可 `launchctl load` 恢复），回填即刻停；**已写入正式记忆库的 270 张旧会话卡需另做清理/降级**（尚未盘点哪几张与当前状态冲突）。

**未决前提**：选项 1 与 3 都需要用户先回答一个问题——**2026-10-19 之后的 ~2000 个会话，是否应该进正式记忆库？** 若「应该」，则本卡所述不是污染而是**积压**，只需加节奏控制（每日配额）而非急停；若「不应该」，则选项 3 优先。

## 7. 复诵三必核（不凭记忆）

- Gmail **57 封逐封实拉**（`format=metadata` 池 8 路 + 新到 6 封 `format=full` 实拉正文，非照抄上轮口径）；
- RED 全量 **458 封实查**（`?from-agent=compass` 端点实测忽略该过滤 → 返回全库；本地按 `to_agent` 分组取增量 `id>93600`，逐封读正文）；
- distill 全部结论来自**现场实物**：`git show`/`git diff --stat`/`ls -lt` 记忆库/`launchctl list`/plist 原文/log 原文/`incremental_stats.jsonl` 逐行解析/`argparse` 实读/`collect_pending` 源码行号引用/桶内 `mtime` 实测。
