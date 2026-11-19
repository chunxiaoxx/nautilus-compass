# INC_20261119 · CI 盲区第二次复发（18 笔未 push 提交）+ 磁盘跌破 10Gi alarm 线

> 轮次：compass loop 值守轮 **R575**（2026-11-19 11:20–11:50 EDT）
> 纪律来源：R573「CI 绿须核 head_sha==被检提交」+ R574 补前置纪律「**每笔提交至少触发一次 CI**」
> 本档只记本轮实测读数与处置，原始历史保留，不改写他轮结论。

## 一、🔴 CI 盲区第二次复发（比 R574 规模更大：3 笔 → 18 笔）

开工 `git status -sb` = `main...origin/main [ahead 18]`（R574 收尾时为 0 领先，已闭环）。

未 push 的 18 笔（提交时点 2026-11-19 09:19–09:33 EDT，产出源=跨对话会话，未更新 loop 留痕轴）：

| # | sha | 标题 |
|---|---|---|
| 1 | `5c5bd5d8` | audit: refine V5 provider gate |
| 2 | `c5a1ce36` | audit: record V5 provider auth boundary |
| 3 | `5940a8e5` | audit: update cross-dialog P0 boundaries |
| 4 | `8cf719f0` | audit: bind Platform gate to OSS artifact failure |
| 5 | `de233b0d` | audit: record V5 provider execution boundary |
| 6 | `d13a739e` | audit: bind V5 gate to concrete chat failure |
| 7 | `8a4489c4` | audit: record V5 chat execution failure |
| 8 | `cdd760de` | audit: define organization goal contract |
| 9 | `3650565e` | audit: sync cross-dialog organization state |
| 10 | `7c39c65a` | fix: normalize VerifyPack relative paths |
| 11 | `12697ade` | assay: sign context capsule verification pack |
| 12 | `60da22fc` | feat: add project-scoped context capsule |
| 13 | `20c7ac60` | audit: isolate stale Compass MCP connector |
| 14 | `e229a6ab` | audit: record MCP recall timeout boundary |
| 15 | `786ef6a9` | audit: add organization continuity snapshot |
| 16 | `7b570e72` | docs(roadmap): clean migration roadmap formatting |
| 17 | `8e5dfb45` | docs(roadmap): turn migration failures into evolution gates |
| 18 | `03df511d` | docs(assay): audit compass 3x capability adoption |

触及面：新增 `tools/context_capsule.py`(216 行)、`tools/org_continuity_snapshot.py`(312 行)、
`tests/test_context_capsule.py`、`tests/test_verifypack/test_cli_e2e.py`、
`runtime/org-continuity/**`(含 context capsule / verification pack / 公钥 / 复现脚本)、
`tools/verifypack/cli.py` 改动，合计 29 文件 +2341/−1 行。

**push 前实测**（遵 R574 前置纪律）：

```
gh api "repos/chunxiaoxx/nautilus-compass/actions/runs?head_sha=5c5bd5d8…"  → total_count = 0
```

⇒ 这 18 笔（连同其父 `f4c00fac` 之后的所有提交）**CI 从未跑过一次**。R574 立的「每笔提交至少触发一次 CI」
前置纪律本轮被再次违反 —— 说明**该纪律只写在档里、没有被任何自动闸执行**，跨对话会话无感。

## 二、🔴 push 前本地复跑 CI 等价集 → 抓到 4 条 F401（main 若直接 push 必红）

R573 的同款坑（`tools/distill_pilot/semantic_review_worker.py` 3 条 F401）**换文件复发**：

```
F401  tests/test_context_capsule.py:1        json
F401  tools/org_continuity_snapshot.py:16    os
F401  tools/org_continuity_snapshot.py:20    sys
F401  tools/org_continuity_snapshot.py:21    time
```

**安全核验（先核后改，沿 R573 协议）**：

- AST 核 `ast.Name` uses：4 个名字全部 `uses=False`；
- 模块级引用：4 个名字在模块顶层 **零引用**（`sys.path.insert` 只出现在 `tests/test_context_capsule.py:5`，
  该文件的 `sys` 是**真在用**，故只删 `json`；`tools/org_continuity_snapshot.py` 里 `os/sys/time`
  仅出现在 import 行，删后无任何行为变化）；
- grep 复核：`--max-time` 是 curl 参数串里的字面量，与 `time` 模块无关。

**修复 = 删 4 行未使用导入**，commit `5b6bdf94`（pathspec 限定，只含这两个文件）。

**改后 CI 等价本地集全绿**：

| CI job 对应命令 | 本地读数 |
|---|---|
| `ruff check .` | `All checks passed!`（.venv ruff 0.17.1） |
| `pytest -q tests/test_mcp_server.py tests/test_a2a_adapter.py tests/test_merkle_chain.py tests/gep` | **453 passed** |
| `python tests/test_compass_v09.py` | **7/7 passed** |
| `python sdk/a2a_adapter.py selftest` | `"status":"ok"` |
| `pytest -q tests/test_context_capsule.py tests/test_verifypack/test_cli_e2e.py`（本批新增测试） | **9 passed** |

⇒ 与 R573 同法：**先把红挡在 push 之前**，main 不经过一次红 run。

## 三、🔴 闭环（绑定核验）

普通 push（未 force）`d372bde2..5b6bdf94`（19 笔）→ CI run **44566551790**，
`head_sha = 5b6bdf948ea85b07f3eca042ffa68576ab2d9e0e` **== 本地 HEAD == origin/main tip** ⇒
绑定成立（不是「CI 列表里最近一笔绿」这种过期读数）。

> 闭环终态见本文末「CI 终态复核」小节（留痕提交自身亦须触发一次 CI，故留痕 commit 再推一笔并复核）。

## 四、🔴 磁盘 avail 跌破 10Gi alarm 线

`df -h /System/Volumes/Data` → **avail 8.6Gi**（容量 98%）。

- R574 记 12Gi → 本轮 **−3.4Gi**（约 6.5h 内），**首次跌破 10Gi alarm 线**；
- 历史基线：11-10 曾达 avail 5.8Gi（掉速 5.3GB/h），根因记为 OrbStack 容器 VM 映像（`data.img.raw`≈460GB），
  属**容器 IO 合计 20GB 排除疯写源**的量级；本轮**未做清理**（零删除，候用户），仅报警；
- 本轮 `du ~/Library/Containers/com.orbstack.OrbStack` 因 TCC 权限/耗时未取到读数（命令超时后置后台）⇒
  本轮**不对根因下新结论**，沿用 11-10 实测基线并标注「本轮未复测」。

## 五、值守面读数（本轮实测）

| 面 | 读数 | 与 R574 比 |
|---|---|---|
| platform 信箱 compass | **0 未读** | 持平 |
| platform RED `check --to platform` | total **234**（R574 232）·新函 `id112704 soul-distress-202611191932`(**96 consecutive**)、`id114042 soul-distress-202611192248`(**97 consecutive**) | **distress ×95→×97** |
| Gmail | 首探 **401** → 直刷 **REFRESH_OK expires_in=3599s** → 7d 全量 **47** 封 / 未读 **30**（双口径 `q=is:unread` = 30 vs 逐封 `labelIds` = 30，**symdiff=0**） | 未读 +3（=新到 3 封） |
| Gmail 新到件（>11-19 08:52Z） | `11-19 12:00Z` Product Hunt 讨论通知 · `11-19 12:50Z` Infini 验证码 · `11-19 15:02Z` Reddit Ads webinar | **3 封全为营销/服务通知类 ⇒ 零新商务函、零新面孔** |
| GitHub mentions | 5 条全旧（最新 11-02 OWASP#35） | 持平 |
| GitHub notifications | **46**（首条仍是 11-19T02:57:35Z 的 CI 失败**过期通知**，对应 run `44447592289` head=`fde3c74a`，已被 R573 修） | 持平 |
| genesis_watch | 5 家 1/1/0/1/2 **零 REPLY** | 持平 |
| dev.to | 30 文 / **8 评论**(6+2) 持平 | 持平 |
| daemon / watchdog / 注入哨兵 | 9876 绿 · watchdog exit 0 · 哨兵 exit 0（recall_hit=**79**） | 持平 |
| GATE0 | `ops/ali30q/verify_criteria_lock.py` → **GATE0 PASS** | 持平 |
| 快筛 | CS-515~518 **存在不过筛**（CS-518 梯度 25.0pp ✓④✓⑤ ✗③） | 持平 |
| 矩阵 | mtime 仍 **10-30 09:42** 停摆 | 持平 |
| rounds.log | `---- round end 11-19 06:49 ----` / `---- round end 11-19 09:19 ----` 两个标记**无内容块**（09:19 与跨对话会话提交时点重合 ⇒ 不判为空转） | 新增 2 处留痕缺口标记 |

## 六、本轮动作与未动项

**动作**：①pathspec 限定 commit `5b6bdf94`（删 4 行未使用导入）②普通 push 19 笔 ③核 CI head_sha 绑定
④留痕（rounds.log / state.json / queue.md / COLLAB_BOARD / 本档 / 记忆卡）。

**未动**：`daemon.py`/plist/symlink 未改 · 未 bootout · 未移 LaunchAgents · 未删任何记忆卡 ·
未碰 NAS · 未外发邮件 · 未 PATCH dev.to · 未动 `.soul-pause` · 未改 workflow ·
他线 6 个未提交文件（`tools/distill_pilot/extract_sample.py`、`tools/distill_pilot/publish_to_memory.py`、
`tools/fuel_intake.py`、`tools/p3_delta.py`、`.codex/config.toml`、`runtime/production_loop/state.json`）
保持 M **未裹挤**。

## 七、候拍板（沿用 + 本轮新增）

1. 🔴 **CI 盲区闸自动化**（本轮新增·最优先）：R573→R574→R575 **同坑三次复发**，全靠 loop 轮人工巡检
   才发现。建议加 pre-push hook 或 CI 侧「分支落后 origin 则不判绿」闸，把「每笔提交至少触发一次 CI」
   从档面纪律变成机器执行。
2. 🔴 **CI ruff 版本未 pin**（三次复发共用放大器）：CI `pip install ruff` 取最新版，本地 .venv 0.17.1 ⇒ 规则集漂移风险。
3. 🔴 **磁盘 avail 8.6Gi 跌破 10Gi**（本轮新增）：零清理候用户；建议 `~/mnt/nas-work2` unmount + OrbStack 映像处置。
4. 🔴 distress **×97** 人监门（人工删 `.soul-pause`）。
5. 🟡 a2a-x402#198 草稿审批 · Gmail 草稿审稿 · 模真真三诉求 · 矩阵 phase2 解锁 · py-spy 仍缺 ·
   review-worker pending 未审 · 复灌 plist 仍在加载目录。

## CI 终态复核

（本节由留痕 commit 触发后回填，见 rounds.log 同轮「CI 闭环实测」行。）
