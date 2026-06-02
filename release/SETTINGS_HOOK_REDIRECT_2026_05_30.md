# Plan A+ surgical · settings.json Stop hook redirect to repo · 2026-05-30

## 触发

Fresh session 2026-05-30 priority #1 = verify H.1 stop_hook auto_ack wire 是否真活
(handoff `session_20260530-0440_compass_v3_phase1de_complete_handoff.md` 标的 5
unverified verification gaps 之一)。

## Finding A 确认 (plugin install vs repo lineage 分叉)

`~/.claude/plugins/nautilus-compass/` 是独立 git workdir on `main` branch
@ 8551756 (v1.7.3 lineage · 含 agentmemory fuse 9-hook dead code) · 不是
Claude marketplace install (`~/.claude/plugins/installed_plugins.json` 不含
nautilus-compass 条目)· dirty 状态:

- 9 modified file (含 stop_hook.py / contract.py / recall.py 等)
- 30+ untracked dirs (drift/ judges/ recall_pkg/ skills_pkg/ bin/cli_l1_*.py 等
  手动 ship 历史痕迹)

repo `C:/Users/chunx/Projects/nautilus-compass` 跑 v3-full-fusion branch
@ 6037244 含 5/29-5/30 sprint 的 5 commit (D.fix-1..4 / E.fix-1..3 / H.1)。

Settings.json 注册的 3 hook script 路径都指 plugin install · 所以 production
hook 跑的是 v1.7.3 lineage stop_hook · 不接 H.1。

verify gap evidence:

- `drift_mitigation_log.jsonl` sidecar 754 fires + 12 ack · 全部 ack
  `source: feedback_cli` (E.fix-3 user CLI path)· **0 行 source: stop_hook_auto**
- plugin install `drift/` dir 只有 `__init__.py / gate_act.py / routing.py`
  · 缺 `auto_ack.py / act_log.py` (H.1 / E.fix-1 都在 repo `drift/` 下)

## Plan A+ 决策

四选项中 user 拍 Plan A+ (settings.json redirect Stop hook 到 repo · 加 surgical
sys.path patch · plugin install 不动留作 fallback):

- 风险最低 (不动 dirty plugin install workdir)
- single source of truth = repo
- anchor #3 反 D 维护 + #5 不重复造轮子最 align
- 估 ~15-30min ship + verify

弃用选项: (a) backport v1.7.x / (b) git checkout v3-full-fusion in plugin
install / (c) nuke + fresh clone · 都有 dirty workdir 冲突风险或时间成本高。

## 2 edit ship

### 1. `~/.claude/settings.json` line 54 · Stop hook 路径

```diff
-            "command": "py -3 C:/Users/chunx/.claude/plugins/nautilus-compass/stop_hook.py",
+            "command": "py -3 C:/Users/chunx/Projects/nautilus-compass/stop_hook.py",
```

UserPromptSubmit (`hook.sh`) + PostToolUse (`mid_session_hook.py`) 路径不动
(surgical · 减小 surface · 那两个 hook 不含 H.1 / D.fix 改动 · 复用 plugin
install 副本 OK)。

backup 副本: `~/.claude/settings.json.bak-pre-plan-a-redirect-20260530`

### 2. `stop_hook.py` main() · sys.path 优先 script 自身路径

```diff
 def main():
     sys.path.insert(0, str(PLUGIN_DIR))
+    # Plan A (2026-05-30) · let repo-resident H.1 / D.fix / E.fix modules win
+    # over plugin install when settings.json hook redirects Stop here. Script
+    # dir goes in last → sits at sys.path[0] → Python finds drift/auto_ack.py
+    # before plugin install's drift/ (which only has gate_act.py + routing.py).
+    sys.path.insert(0, str(Path(__file__).resolve().parent))
     from strategy_store import StrategyStore
```

`PLUGIN_DIR` 仍指 plugin install · sidecar 文件 (`drift_mitigation_log.jsonl`
等) 写入路径不变 · daemon 端 fire 和 stop_hook auto_ack 仍写同一个文件 ·
`act_on_rate` 计算可 join 两侧。

`Path(__file__).resolve().parent` 在 plugin install 跑时 = plugin install 路径
(self) · 在 repo 跑时 = repo 路径 · 两份代码同时存在不冲突。

## Verify · BEFORE vs AFTER

```
ack count (source=stop_hook_auto):
  BEFORE: 0
  AFTER:  3
  delta:  +3 (matches stdout "emitted 3 drift ack(s)")
```

Smoke test stdout:

```
[stop_hook auto_ack] emitted 3 drift ack(s) · a-4250a122=fp, a-82e301c5=fp, a-90f269d5=fp
[stop_hook contracts] scanned 86 files · outstanding=1 consumed=3 expired=0 · close_loop_mean=79.53h
```

3 ack 都从 latest session memory `session_20260530-0440_compass_v3_phase1de_complete_handoff.md`
extract (handoff §6:00 PDT addendum 预测的就是这 3 个 alert_id)。算法正确。

D.fix scanner 也活了: 86 files 720h glob · 4 协议解析 (含 metadata.contracts
nested + singular contract_id + close_loop:true 等)。

## 5/27 drift loop closing 真正闭环

| measurement side | impl | first-data ts |
|---|---|---|
| detection | recall.py:159 daemon writer | 2026-05-22 (上线 v3 detection) |
| intervention · user CLI path | E.fix-3 feedback.py:cmd_log | 2026-05-30 04:00 PDT |
| intervention · agent self-ack path | H.1 stop_hook auto_ack | **2026-05-30 14:26 PDT (本次)** |

3/3 闭环完整。act_on_rate 现可在两个 source 上都测量。

## 真实 act_on_rate 现状 vs target

- 历史 fire: 754 (含 history)
- 7d window fire: 298
- 7d window ack: 15 (12 feedback_cli + 3 stop_hook_auto)
- 7d act_on_rate: ~5.0% (按 fire/ack 直接比)
- target: ≥70%
- gap: ~14x

vs handoff 5/30 06:00 PDT 估的 1.3% (假设 Stop event 触发后) · 实际 manual smoke
test 已涨到 5.0% · 涨幅 ~4x 优于预期。

## 后续监控

- 等下次真 Stop event (本 session 结束 / 下个 fresh session 起来) 看 stop_hook_auto
  ack 是否随每次 Stop 真增长 · 24h-7d window 趋势
- 若涨势远低于预期 (e.g. 1-2 ack per session) 看 Finding E (session_writer 是否
  truncate ack text · 影响 extract_acks_from_text input completeness)
- Finding F (D.fix-4 是否真识别 close_loop:true) 现 smoke test 显示 contract
  count 跟 handoff 不一致 (outstanding 1 vs 2 / consumed 3 vs 2)· 可能 D.fix-4
  已 covered · Finding F 可能假设错 · 待 next session 细 audit

## Caveat / known gaps

- UserPromptSubmit (`hook.sh`) + PostToolUse (`mid_session_hook.py`) 仍跑 plugin
  install v1.7.3 lineage 版本 · 未来若 repo 端这俩文件有重要改动需要类似 redirect
- Plugin install 仍 dirty workdir · 真 Plan B/C 清理留作未来 release cleanup task
- `__init__.py` 在 repo 还显示 `__version__ = "2.0.1"` · 没 bump 到 3.x · 因为
  Plan A+ 不动 plugin install · 不影响 deployment · 但 next release 应 bump
- session_writer.py 跑 LLM distill call ARK API 400 error (背景 noise · 不影响
  H.1)

## 关联 anchor / memory

- anchor #2 递归自我提升闭环优先 (intervention measurement 真闭环)
- anchor #3 反 D 维护 (不 backport v1.7.x · 让旧 lineage 自然 EOL)
- anchor #5 不重复造轮子 (settings.json 1 line redirect 复用 repo)
- anti-pattern "deploy 完了 但没验证版本号" / "把 v3.0 老代码部署上去当 v3.5" (本
  release 是直接对治: BEFORE/AFTER 硬数据 verify · 不假装 ship)
- handoff `session_20260530-0440_compass_v3_phase1de_complete_handoff.md`
  §6:00 PDT addendum (本 release 闭合该 handoff Finding A unverified gap)
