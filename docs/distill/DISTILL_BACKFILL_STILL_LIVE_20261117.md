# 🔴 distill 旧会话回填·R557 审计后复核（2026-11-17 R558 值守轮）

> 承接卡：[`DISTILL_LIVE_BACKFILL_RISK_20261116.md`](DISTILL_LIVE_BACKFILL_RISK_20261116.md)（R557 追记）。
> 本卡只记 **R557 审计之后** 的新增实测事实与增量结论，不复述原卡全文。
> 结论标注：[实测]/[他测]/[推断]。**本轮零生产动作**（未停/未改 launchd，未改他线未提交文件，未改任何生产配置）。

## 0. 一句话

**他线已自行提交 freeze 修复，但旧会话回填未停、线上仍跑未提交代码、选择面未收口** —— R557 的风险未闭环。

---

## 1. 他线已推 freeze 提交[实测]

```
dd821259 fix(distill): freeze evidence-bound incremental pipeline
  Author: chunxiaoxx <chunxiaoxx@gmail.com>
  Date:   Tue Nov 17 02:09:22 2026 -0500
  tools/distill_pilot/compress_arm.py        |  51 +++-
  tools/distill_pilot/incremental_distill.py | 412 +++++++++++++++++++++--------
```

- R557 提出的四选项，他线选择了「自行修 freeze」路线（未与 compass 协调）。
- 同批另有 3 个他线提交：`0b7a16d3` 四对话框 rollout 计划、`39c7d01d` 只读 Mac 对话框盘点、`ad32b86f` 多对话操作协议。
- 本地 HEAD=`dd821259`，`origin/main`=`bd7c2541` → **本地领先 4 个他线提交未推**（本轮未替他线推送，见 §6）。

## 2. 旧会话回填**未停**[实测]

R557 审计完成时间 11-16 22:12 EST。审计之后仍新增 3 张 distill 卡进**正式记忆库**：

| 卡 | 源会话 jsonl mtime | 距今 |
|---|---|---|
| `distill-d2e59280-…` | 2026-10-19 23:54 | 28 天 |
| `distill-20d22a23-…` | 2026-10-19 23:53 | 28 天 |
| `distill-ff33617d-…` | 2026-10-19 23:51 | 28 天 |

- 记忆库总卡数 **1409 → 1413**（+4，含本轮写入的审计记忆卡 1 张）；`find -mtime -1` = 23 张。
- 线上日志 `runtime/scratch_distill_pilot_20261104/incremental.log`（mtime **11-17 02:11**）末行 `[incr] ff33617d published`。
- 关键时序：**freeze 提交 02:09:22 → 线上 02:11 一轮照旧 published** ⇒ 新代码路径仍会发布旧会话。

## 3. 新旧代码行为对照[实测]

`git show dd821259:tools/distill_pilot/incremental_distill.py`：

- **B2 部分收口**：新增 `publication_valid()`（校验 receipt 的 `source_sha256` 与落盘文件 sha256 一致）、`cache_valid()`、`publish_revision()` 写回执、`review_required` 分支处理 —— 发布动作**有回执可验**，R557 指出的「source_sha256 只记不校 / 复核分支不可达」在代码层已修。
- **B1 选择面未收口**：新 `collect_pending()` 的排除条件只有 4 条 ——
  `st_size < MIN_SIZE`、`now - mtime < WRITING_WINDOW`（写入中）、`PATROL_RE` 命中、`source_sha256` 命中且缓存/发布有效。
  **没有任何时间下界**（不排除 >7d 旧会话）。桶内实测 **2038 个 jsonl，其中 1941 个 >7d（95%）** 仍全部进入候选。
  → 语义从「mtime 水位」换成「内容哈希」，是**证据绑定**的改进，但**存量旧会话仍会被逐张写进正式记忆库**（每会话至多一次，约 12 卡/天）。
- **B3/B4 所在文件仍未提交**：`p3_delta.py`（+57 行）不在 dd821259 内，仍在工作区未提交态。

## 4. 🔴 「线上跑未提交代码」**部分仍成立**[实测]

`incremental_distill.py:21-24` 的 live import 链：

```
from anchor_check import …
from compress_arm import compress_session      ← 已随 dd821259 提交
from extract_sample import extract_file         ← 未提交(+188)
from publish_to_memory import MEMORY_DIR, …     ← 未提交(+243，正式记忆库写入方)
```

工作区未提交文件（`git diff --stat tools/`，本轮**未触碰**）：

```
tools/distill_pilot/extract_sample.py    | 188 +++++
tools/distill_pilot/publish_to_memory.py | 243 +++++
tools/fuel_intake.py                     |   5 +
tools/p3_delta.py                        |  57 ++
```

⇒ **真正写正式记忆库的 `publish_to_memory.py` 与抽样的 `extract_sample.py` 仍以未提交态在线上执行**。

## 5. 线上任务现状[实测]

- `launchctl list` → `com.nautilus.distill-incremental` **仍加载**（当前非运行态，上次退出码 0）。
- plist：ProgramArguments 直接指向工作区 `tools/distill_pilot/incremental_distill.py`，`--max-sessions 1`，`StartInterval 7200`，`RunAtLoad false`，plist mtime 11-16 11:12。
- 下次触发 ≈ **11-17 04:11 EST**。
- 未见任何「暂停/冻结开关」痕迹（`grep dirty|git status|HEAD|freeze|frozen|worktree` 在新 `incremental_distill.py` 中**零命中**）⇒ 该提交未加工作区洁净守卫。

## 6. 本轮零动作声明

停/改 launchd、改他线未提交文件、推送他线提交 —— 三者均为他线生产状态变更，按红线与「候用户拍板」纪律**本轮一律未做**：
- 未 `launchctl unload/stop`，未改 plist；
- 未 `git add`/`commit`/`checkout` 他线 4 个文件的工作区改动（保持 ` M` 原样，未裹挟落账）；
- 未 push（本地领先 4 个他线提交原样保留）。

## 7. 候用户裁定的三个收口选项（供拍板，本轮未执行）

1. **选面收口**：给 `collect_pending()` 加时间下界（如只取 >7d 的排除 / 只取 patrol 新会话），把 1941 张旧会话存量挡在正式记忆库之外；存量可另置「归档区」而非正式库。
2. **未提交收口**：他线把 `publish_to_memory.py` / `extract_sample.py` / `p3_delta.py` 落账，或给 launchd 改指向 HEAD 固定副本（`git worktree`/release 目录），使「线上跑什么」可审计。
3. **动作收口**：若不再需要该管线 → `launchctl bootout`（可 `launchctl load` 恢复），回填即刻停；记忆库已写入的 ~25 张旧会话卡需另做清理/降级（尚未盘点）。

## 8. 复诵三必核（不凭记忆）

- Gmail **58 封逐封实拉**（`format=metadata` + 线程池 8 路，非照抄上轮口径）；
- RED 窗口 `check --to platform` **211 封实查**，以 id>92414 取增量；
- distill 全部结论来自**现场实物**：`git show` / `git diff --stat` / `find` / `launchctl list` / plist 原文 / log 原文 / 记忆库目录 `ls`。
