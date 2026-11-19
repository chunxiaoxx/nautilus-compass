# INC_20261119 · 未 push 提交造成 CI 盲区(R574 值守轮实测)

> 状态:已闭环(main CI 绿,head_sha 绑定实测)
> 轮次:loop R574(2026-11-19 04:29–04:5x EST)
> 类型:检测缺口 · 留痕 · 纪律补强

## 一句话

11-19 03:40–04:21 的跨对话会话提交了 3 笔(含 `daemon.py` 生产改动)但**未 push**,
⇒ 这 3 笔**从未触发过 CI**;R574 值守轮补推并实测核 `head_sha` 绑定后 CI 全绿。

## 一、事件(实测)

- 本地 `git status -sb` = `main...origin/main [ahead 3]`,`git log --oneline origin/main..HEAD` = 三笔:
  | commit | 标题 | 触及面 |
  |---|---|---|
  | `91850f2a` | perf(compass): bound interactive rerank context | `daemon.py`、`ops/launchd/com.nautilus.compass-daemon.plist`、`COLLAB_BOARD.md`、`runtime/cross-dialog-receipts/20261119-R574.json` |
  | `3c80cd1e` | docs(compass): clarify same-host rerank topology | 同上 + daemon.py 注释 |
  | `f4c00fac` | test(compass): record local rerank quality probe | 新增 `tools/benchmark_rerank_latency.py`(189 行)、`runtime/cross-dialog-receipts/20261119-rerank-ab.json`(845 行) |
- push 前实测:`gh api "repos/chunxiaoxx/nautilus-compass/actions/runs?head_sha=f4c00fac3b34ddc88881a5828dcc54fa915b37f3"` → `total_count=0`
  ⇒ **这三笔(含生产 daemon 改动)CI 从未跑过**。
- 该跨对话会话写了 COLLAB_BOARD 三行(03:40 / 04:00 / 04:21),但**未更新** `runtime/loop/state.json` 与 `runtime/loop/rounds.log`
  ⇒ loop 留痕轴看不见它,若无人巡检 `ahead` 计数,这批未验证的生产改动会无限期滞留在本地。

## 二、为什么 R573 的纪律救不了

R573 立了「**CI 绿须核 `run.head_sha == 被检提交 sha`**」。该纪律只对**已经跑过的 run** 有效;
对**从未触发 run 的提交**,「核 head_sha」这件事本身无从做起——查出来是 `total_count=0`,而不是某个 mismatch。
⇒ 补一条**前置**纪律:**先确保每笔提交都至少触发过一次 CI**。

## 三、检测与闭环(实测)

1. **push 前本地跑 CI 等价集**(全绿):
   - `.venv/bin/ruff check .` → `All checks passed!`(ruff 0.17.1)
   - `python3 -m pytest -q tests/gep` → `413 passed`
   - `PYTHONIOENCODING=utf-8 python3 tests/test_compass_v09.py` → `7/7 tests passed`
   - `python3 sdk/a2a_adapter.py selftest` → `"status": "ok"`
   - `python3 -m pytest -q tests/test_ci_lint_clean.py` → `1 passed`
2. **push**:`5db29eec..f4c00fac`(普通 push,未 force)
3. **CI run 绑定**:`gh api "…/actions/runs?head_sha=f4c00fac…"` → `total_count=1`,run `44497348634`,
   `headSha=f4c00fac3b34ddc88881a5828dcc54fa915b37f3` == 本地 HEAD == origin/main tip
4. **结论**:`conclusion=success`,**12 个 job 全 success**(含 `Lint`)。
   逐 job:`Lint` / `S4 GEP minimum Python (3.9)` / `Test (Python 3.10|3.12 · ubuntu|macos-latest)` ×4 /
   `v0.9 Cursor extension build` / `v0.9 integration tests` / `v0.9 npm wrapper` /
   `v1.0 MCP + A2A protocol pytest` / `v1.0 MCP server (10 tools)` / `v1.0 V7 governance demo (lock+dispatch+audit)`

## 四、同族坑(均本轮实测)

| # | 坑 | 现象 | 正解 |
|---|---|---|---|
| ① | **GitHub CI 失败通知是过期读数** | `gh api notifications` 首条「CI workflow run failed for main branch」(updated 11-19T02:57:35Z) | 该通知对应 run `44447592289` head=`fde3c74a`(R572 提交),**已被 R573 修复**并被 `44479046804`(head=1ebf465e)/`44479511335`(head=5db29eec) 两笔绿 run 覆盖 ⇒ 必须 `gh run view <id> --json headSha` 回到 run 层核 |
| ② | **`plutil` 读嵌套键缺前缀** | `plutil -extract COMPASS_RERANK_CANDIDATES raw <plist>` 报「No value at that key path」 | 键在 `EnvironmentVariables.` 之下 ⇒ `plutil -extract EnvironmentVariables.COMPASS_RERANK_CANDIDATES raw`。差点误判为「已装 plist 缺新配置 = 仓/线上漂移」 |
| ③ | **R 编号跨轴撞号** | COLLAB_BOARD 已有三行「compass R574」(03:40/04:00/04:21),与 loop 轮次 R574 同号 | 两者属不同留痕轴(跨对话任务 vs loop 轮);本轮不改写他行,只在 queue/rounds.log 标注区分 |

## 五、仓/线上漂移核验结论(实测,均为「无漂移」)

- 仓内 `ops/launchd/com.nautilus.compass-daemon.plist` 与已装 `~/Library/LaunchAgents/com.nautilus.compass-daemon.plist` → **逐字节相同**
  (含 `COMPASS_RERANK_CANDIDATES=16` / `COMPASS_RERANK_MAX_LENGTH=512`)。
- 插件副本 `~/.claude/plugins/nautilus-compass/daemon.py` 与仓内 `daemon.py` → sha256 **相同**(`701152b7…`)
  ⇒ `91850f2a` 的 rerank 上下文收紧改动**确在跑的进程里**(launchctl 实测 PID 31330,label `com.nautilus.compass-daemon` 在册)。

## 六、纪律补强(建议纳入 loop 轮固定动作)

loop 轮开工检查项,在既有值守渠道之外并列一条:

```
git status -sb | grep 'ahead'  → ahead>0 时:
  ① git log --oneline origin/main..HEAD        # 列出未验提交
  ② gh api ".../actions/runs?head_sha=<tip>"   # total_count==0 ⇒ 从未验证
  ③ 跑 CI 等价本地集 → push → 轮询 run 至 completed 且 headSha==HEAD
```

## 七、零生产动作声明

本轮未改 `daemon.py` / plist / symlink · 未 bootout · 未移 LaunchAgents · 未删任何记忆卡 · 未碰 NAS ·
未外发邮件 · 未 PATCH dev.to · 未动 `.soul-pause` · 未改 workflow。
本轮唯一动作 = **补推既有提交 + 核 CI + 留痕**;他线未提交文件(`tools/distill_pilot/*`、`tools/fuel_intake.py`、
`tools/p3_delta.py`、`.codex/config.toml`、`runtime/production_loop/state.json`)保持 M 未裹挟。
