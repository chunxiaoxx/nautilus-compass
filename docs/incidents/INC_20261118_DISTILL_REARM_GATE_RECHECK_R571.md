# INC_20261118 · distill 复灌向量降级 + 存量计数勘误（R571 值守轮 · [实测]）

> 承接：R557-R559（线上跑未提交代码 / 回填未停）→ R568（写入侧四环实测·止血）→ R569（同口径 top30 复算结清·读取侧已自愈·库级存量未清）→ R570（值守持平）
> 本卡只做两件事：①独立复核"写入侧止血"是否**持续**（而非一次快照）；②把"复灌"候拍板项的**残余危害上限**用代码级证据钉死。
> 全部结论标 [实测]；未做的动作照实写"未做"。本轮**零生产动作**。

---

## 一、写入侧止血持续性复核（推进 R569 欠账）

| 观测项 | 命令/口径 | 实测 | 与上轮对比 |
|---|---|---|---|
| 记忆库总卡数 | `find <mem> -maxdepth 1 -name '*.md' \| wc -l` | **1431** | R569 1431 持平 |
| distill 卡数 | `find -name 'distill-*.md'` + `ls \| grep -c '^distill-'`（双口径） | **314 / 314** | R568 314 持平；**R569 记 306 有误** |
| session_auto 卡数 | `find -name 'session_auto_*'` | **883** | R569 883 持平 |
| 最新 distill 卡 | `find -name 'distill-*.md' -newermt "2026-11-18 08:46"` | **0 张** | 最新仍 11-18 08:45 |
| 08:46 后新增任意噪声卡 | 同上 `-newermt "2026-11-18 08:46"`（distill-* + session_auto_*） | **0 张** | — |
| 运行进程 | `ps aux \| grep incremental_distill` | **无** | — |
| 装填态 | `launchctl list \| grep distill` | 仅 `com.nautilus.distill-review-worker`（PID 列 0=当前未驻留）⇒ **distill-incremental 未加载** | R568/R569 一致 |

**[实测] 写入侧止血已连续保持 11h12m**（08:45 → 20:00 EST）：按回填节律约 2h/张，本应新增约 5 张，**实测 0 张**；库总数与噪声存量**零增长**。
⇒ R569「持续累积」结论继续不成立，且本次为**跨轮持续性**验证（不是单点快照）。

---

## 二、计数勘误（R569 → R571）

R568 记 `distill-* 314`，R569 记 `distill 306`，二者互斥。本轮双口径（`find`/`ls`）**均为 314**，且 08:46 之后**零新增、零删除** ⇒
**R569 少计 8 张属口径/计数错误，不是期间发生删除**（删除会留下 mtime 痕迹，且总量应减）。

| 口径 | R568 | R569 | R571（本轮双口径复核） |
|---|---|---|---|
| distill-* | 314 | 306 ❌ | **314** |
| session_auto_* | 883 | 883 | 883 |
| 噪声合计 | 1197 | 1189 ❌ | **1197** |
| 占 1431 比例 | 83.7% | 83.1% ❌ | **83.7%** |

⇒ 候拍板项「存量噪声卡清理」的正确数字是 **1197 张 / 83.7%**，清理口径与命令须按此重算。

---

## 三、复灌向量：现状 + 残余危害上限

### 3.1 现状 [实测]

```
~/Library/LaunchAgents/com.nautilus.distill-incremental.plist   (mtime 11-16 11:12, 仍在加载目录)
launchctl list | grep distill-incremental  →  无该 label（未加载·bootout 生效）
ps aux | grep incremental_distill         →  无进程
```

⇒ **当前无回灌**；但文件留在 `~/Library/LaunchAgents` ⇒ macOS 登录时 launchd 会重新装载该目录内的 plist ⇒ 存在**登录后复灌**向量。

### 3.2 勘误 R569 一处细节

R569 记「plist `RunAtLoad` ⇒ 当前未加载但下次登录即复灌」。`plutil -p` 实测：**`RunAtLoad => false`**，`StartInterval => 7200`。
⇒ 复灌**不会在登录瞬间触发**，而是登录后**约 2h**（首个 StartInterval 周期）才首次触发。危害时点后移，结论方向不变。

### 3.3 代码闸门三层已落地（危害上限收敛）[实测]

commit `08af5b02`（11-18 10:39 `fix(compass): gate unverified memory and freeze distill backfill`）起：

| 层 | 代码坐标 | 行为 |
|---|---|---|
| (a) 选择面时间下界 | `incremental_distill.py:33` `AUTO_MAX_AGE_SECONDS`（env `DISTILL_AUTO_MAX_AGE_SECONDS`，默认 7×86400）**真被使用**于 `:164-165` `collect_pending()` | >7d 会话被跳过（除非 `--include-archive`，:373）⇒ **R559 的「无时间下界」在代码层已收口** |
| (b) 发布闸 | `incremental_distill.py:198-206` `publish_revision(review_file=None)` | 无 review receipt ⇒ 直接返回 `status=review_required` 且**不调用** `publish_to_memory.py` ⇒ **无审核回执不能写正式库** |
| (c) 回执绑定 + 回读 | `publish_to_memory.py` 侧校验 `source_sha256` / `summary_sha256` / `anchors_sha256`；`incremental_distill.py:140-152` `publication_valid()` 文件回读校验 | 回执须绑定本次修订并通过回读，否则拒发 |

且 review worker 现状：approved=0 / published=0（全部 `hold`）。

### 3.4 结论 [实测]

**即便登录后复灌，最坏路径 = 把 ≤7d 候选推进到 `review` 状态排队，不再把旧会话噪声卡灌进正式记忆库。**
⇒ 候拍板项「distill 复灌」由 🔴 **降级为 🟡**：残余面 = ①≤7d 候选堆积（队列膨胀，非库污染）；②`publish_to_memory.py`(+243)/`extract_sample.py`(+188)/`p3_delta.py` 仍是**未提交工作区**版本（他线 R557-R560 产物），即"写库那把钥匙"仍未入账——但闸门代码已入账，且无回执不触发。
**本轮未移 plist、未 bootout、未改他线文件**（生产动作候用户拍板；且按代码闸门现状，复灌危害已不构成紧急项）。

---

## 四、留痕与代价

- 本轮零生产动作：未改代码/plist/symlink · 未 bootout · 未移 plist · 未删记忆卡 · 未碰 NAS · 未外发邮件 · 未 PATCH dev.to · 他线 5 个未提交文件保持 M 未裹挤。
- 产出：本卡 + `runtime/loop/rounds.log`（R571 行）+ `runtime/loop/state.json`（round 571）+ `runtime/loop/queue.md`（R718 段）+ `COLLAB_BOARD.md`（R571 行），走限定 pathspec commit。
- 候拍板更新：🔴 distress ×92（人监门）· 存量 **1197** 张噪声卡清理（数字已修正）· 通道配额 · a2a#198 / Gmail 审稿 / 模真真三诉求 · 矩阵 phase2 解锁 · py-spy 仍缺；🟡 复灌（plist 留加载目录，RunAtLoad=false，代码三层闸已收口 → 建议移出或明确接受）。
