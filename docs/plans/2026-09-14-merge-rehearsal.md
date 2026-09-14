# 9/15 三件套合入预演报告(2026-09-14 · RSI 环 #1)

> 预演目的:9/15 手术前先暴露冲突。**结论:原计划「直接 merge feat/memory-gate-trio」不可行,改走 cherry-pick 路线,成品分支 `merge-ready-0915` 已备好并全绿。**

## 一、为什么直接 merge 不行(预演发现)

在 origin/main(f148051)基座演练 merge feat/memory-gate-trio:**10 个核心文件冲突**(daemon.py / mcp_server.py / recall.py / stop_hook.py / mcp_http_server.py / daemon_start.ps1 / ssot_consistency.py / conftest.py 等)。

根因:两线平行演进了同一批生产文件——
- feat 线:45d32a9(8 月底基)→ 云部署/PYTHONPATH/HUD/recall v2.4 → **3912205(9/1 生产 WIP 快照)** → 三件套(b982327)→ J4 基线(9cb9e7e)
- main 线:45d32a9 → 四探针/邮箱验证/双洞修复/tools 收敛/token 修复+HTTP 迁移/3.1.2/ruff → f148051

冲突主体来自 3912205 WIP 快照与 main 安全序列的分叉,**不是三件套本身**(三件套净改动仅 6 文件 409 行,main 线 9/1 后没动过 daemon.py/recall.py 源码)。

## 二、9/15 采用路线(预演已执行)

cherry-pick b982327 + 9cb9e7e 到 main 基座:
- 唯一冲突 `tests/conftest.py`(5 行)已解:main 的 HTTP TestClient fixture 与三件套的 sys.path 注入**两段都保留**
- 成品分支:**`merge-ready-0915`**(= f148051 + 1121328 三件套 + de0552b 基线),位于 memgate worktree

## 三、验证证据(全部实测)

| 验证项 | 结果 |
|---|---|
| 三件套 15 单测 | **15 passed** (2.26s) |
| J4 回归门(新代码 9878 实例,三冻结 fact hit@3) | **GREEN**(命中正确,455/428/518ms) |
| 生产 9876 | 全程未触碰 |

## 四、9/15 runbook 修正版

1. 生产 worktree checkout `merge-ready-0915`(不要 merge feat/memory-gate-trio)
2. 受控重启(测试实例验过后再做生产)
3. `python ops/regression_gate.py` 对照基线(J4 三 fact)
4. J1-J3 读数回填预注册档(docs/plans/2026-09-09-rsi-trial1-preregistered.md)
5. 非实现者复算(RSI 环第四段)
6. 判据只许更严

## 五、环境备忘

- **9877 端口被 P1 迁移 SSH 隧道占用**(9/15 停),测试实例一律用 **9878**(本次已用完清理:实例已停/临时 gate 脚本已删)
- daemon 端口 env:`COMPASS_DAEMON_PORT`;token 默认全局路径,gate 天然对齐
- worktree 预演后已切回 feat/memory-gate-trio,现场干净
