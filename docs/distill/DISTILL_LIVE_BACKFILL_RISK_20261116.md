# 🔴 DISTILL 线上链路审计卡·工作区未提交代码已在生产跑(2026-11-16 R557 值守轮)

> 本卡由值守轮 R557 独立代码审查（只读子代理）+ 本轮实测取证生成。
> 结论标注：`[实测]`=本轮亲自跑出；`[他测]`=审查子代理在沙箱复现；`[推断]`=未直接验证。
> 纪律：本卡不含任何未实测数字；负结果与限制照报。对外/生产动作一律候用户拍板，本轮**未**停任何任务、**未**改任何生产配置。

---

## 一、核心事实：工作区 = 线上（不是"待启用改动"）

`[实测]` launchd 任务 `com.nautilus.distill-incremental` **已加载**，直接执行**工作区未提交文件**：

```
~/Library/LaunchAgents/com.nautilus.distill-incremental.plist
  ProgramArguments = /usr/bin/python3
                     /Users/chunxiao.wang/Projects/nautilus-compass/tools/distill_pilot/incremental_distill.py
                     --max-sessions 1
  StartInterval    = 7200   # 每 2 小时
  plist mtime      = 2026-11-16 11:12（今日）
  launchctl list   = "-  0  com.nautilus.distill-incremental"（已加载，上次退出码 0）
```

`[实测]` 该任务写入的正本是**正式记忆库**：
`~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory` —— 当前 **1409 张卡**，其中 **25 张写于最近 24h**（recall 侧已可见，会话启动即召回）。

> 含义：distill_pilot 这批 11/8-10 的未提交改动**已经在线上生效**，不是待评审的死代码。落账与否不再是"要不要上线"的问题，而是"线上正在跑无版本、未评审的代码"。

---

## 二、阻断级问题（4 条）

### B1. 真实待处理队列 1085 个**全部是 7 天以上旧会话**，且每 2h 放行 1 个 → 约 90 天持续回填

`[实测]` 直接调用 `collect_pending()` 取真实队列（绕过 `--max-sessions` 截断）：

```
pending_total          = 1085
pending_older_than_7d  = 1085      # 100% 是旧会话
newest_pending = 3e11f289…  11-09 12:46
oldest_pending = 7659f5de…  10-18 21:43
```

`[实测]` 关键坑：`select_pending()` 在**打印计数之前**就做了 `pending = pending[:args.max_sessions]`（`tools/distill_pilot/incremental_distill.py:325-326`），所以线上日志里那句 `新增或待发布版本 1` **不是队列长度**，是被 `--max-sessions 1` 截断后的数——照日志读会误判"没有积压"。

`[实测]` 排序为 newest-first（`incremental_distill.py:321-324`），故线上每 2h 吃掉一个"当前最新待处理"，旧会话持续排队。

> 后果量级：**12 卡/天 × 约 90 天**，把 2026-10-18 → 11-09 的历史会话逐批写进正式记忆库。这批历史会话**从未经过语义复核**（见 B2）。

### B2. 语义复核分支在自动链路**不可达**，且 `source_sha256` 从不校验

`[实测]` `publish_to_memory.py:56-96` 的 `validate_review()` 实现本身是完整的（校验 schema/decision/session_id/source_sha256/reviewer/reviewed_at/**源文件哈希**/evidence/checks）——**但线上路径从不传 review 文件**：

- `incremental_distill.py:186-191` 的 `publish_revision()` 调 `publish_to_memory.py` 时**没有 `--review-file`**；
- `[实测]` 全仓检索：`review_file` 的消费方只有 `publish_to_memory.py`，`export_fuel_candidates.py` 属另一条链；**除测试外无任何 review receipt 生产者**。

`[实测]` 结果：`validate_review()` 在自动链路里永不触发 → `source_sha256` 只被**记录**、不被**校验**（校验逻辑只存在于 review 分支内）→ 已发布卡的"证据链"实为调用方自述。

`[他测]` 正式记忆库现有 **252 张**新格式卡，最近 24h 新增 **10 张**（本次 R557 独立复核得 1409 总卡 / 25 张 24h 内，口径不同但同向）。

### B3. `p3_delta` 去重只按 `content_hash`，与导出侧的"修订"语义断链；被拒件每轮重计、永不吸收

`[实测]` `tools/p3_delta.py:105` 去重键 = `content_hash`；而 `export_fuel_candidates.py` 支持"改标签/改复核人"的修订（`candidate_revision_sha256` / `supersedes`）——同 `content_hash` 的修订件在收集器侧被 `h in fps` 直接吞掉，导出侧承诺的修订留痕**到收集器即断**。

`[实测]` 被拒件现在**不再写指纹**（这是相对 HEAD 的行为变更，目的是让"后来被独立纠正的投递"还能再被评估），但**从不 absorb**——空 `fresh` 早退路径不搬 inbox ⇒ 同一被拒件每轮重计，`whitelist_rejected` 由增量退化为存量。

`[他测]` 沙箱复现：投 1 条 `label_origin=self_recompute` ⇒ 连跑 3 次，每次 `"rejected": 1`，文件始终留在 inbox、absorbed 为空、指纹账保持 `[]`。

### B4. `tools/p3_delta.py` 无 argparse ⇒ `--help` 会**真的执行收集器**

`[他测]` `python3 tools/p3_delta.py --help` 未报错而是直接跑了一遍收集器，输出
`{"ts":…,"cycle":3,"verdict":"SKIP","new":0,"rejected":0,…}`，并新建 `runtime/verdict_corpus/delta/{inbox,absorbed}` 空目录、重写 `accepted_hashes.json`。

`[实测]` **repo 未被污染**：`git status --porcelain runtime/verdict_corpus` 为空，`accepted_hashes.json` 与 HEAD 逐字节相同（1494 条）。副作用仅落在未跟踪空目录。

---

## 三、非阻断观察

`[实测]` **时间戳改 UTC 是修 bug，不是破坏**：本机 TZ=EST(-0500)，旧 `strftime("...+08:00")` 是硬写 +08:00 的 13 小时谎报；全仓无人解析 `p3_delta` 的 `exported_at`/`ts`（`p3_ticket` 读 `delta_*.jsonl` 不读 manifest）→ 不破坏下游，仅语料时区混排。

`[实测]` `extract_sample.py:120-129` 三处静默 `continue`（坏行/非 dict）**无计数**，丢件不可见。

`[实测]` `compress_session` 空源 → IndexError（HEAD 已有，非本批引入）；增量链路被 run_batch 的 catch-all 兜住，但 `compress_arm` CLI 只 catch RuntimeError → 整批崩。

`[实测]` `publish_one` 已无调用方（兼容壳）。

---

## 四、候用户拍板（选项，附代价）

| # | 选项 | 代价/影响 |
|---|---|---|
| ① | **保持现状**（不落账、不停任务） | 线上继续跑未版本化代码；12 卡/天 未复核回填持续约 90 天；证据链不实（`source_sha256` 不校验） |
| ② | **仅停 launchd**（`launchctl unload`），代码留在工作区不落账 | 立即止血；蒸馏增量通道停摆（他线产能归零）；一行命令可逆 |
| ③ | **停 launchd + 落账 + 修 B1/B2/B3/B4 后再开** | 最稳但工作量最大；期间无新 distill 卡 |
| ④ | **落账但保持任务停用**（先有版本、暂不产） | 版本化收益，产能仍为零 |

本轮**未执行**任何选项——停/改生产任务属他线生产状态变更，按红线与"候用户拍板"纪律留候。
（`[实测]` 仓库状态：R557 轮次留痕已 pathspec 限定提交；`distill_pilot/*`、`fuel_intake.py`、`p3_delta.py` 及 3 个新测试 + `export_fuel_candidates.py` 仍为**未提交/未跟踪**，按 R556 先例不裹挟落账。）

---

## 五、证据坐标

- 未提交改动：`git diff --stat tools/` = 6 文件 +758/-198；新增未跟踪 `tools/distill_pilot/export_fuel_candidates.py`、`tests/test_distill_{publication_review,tool_evidence}.py`、`tests/test_memory_fuel_candidates.py`（**3 新测试实测 37 passed**）。
- launchd：`~/Library/LaunchAgents/com.nautilus.distill-incremental.plist`；日志 `runtime/scratch_distill_pilot_20261104/incremental.log`（90 次运行抬头 / 261 published / 76 review；日志头可见早期 `GATED: DISTILL_GREEN 不在` 段）。
- 正式记忆库：`~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory`（1409 卡 / 24h 内 25 张）。
- 队列实测：`collect_pending(BUCKET, RUNTIME, load_state(RUNTIME, MEMORY_DIR))` → 1085 / 全部 >7d。
- 代码坐标：`tools/distill_pilot/incremental_distill.py:147-175,186-191,316-327`；`tools/distill_pilot/publish_to_memory.py:56-96,100-112`；`tools/p3_delta.py:93-125`。
- 全量 pytest 在本机 py3.9 因 PEP604 语法收集错 23 项（**预存环境问题**，与本批改动无关）；本机 Python 3.9 为历史遗留，CI 侧不阻塞。
