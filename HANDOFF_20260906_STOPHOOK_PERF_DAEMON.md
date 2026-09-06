# HANDOFF 20260906 — Stop hook 每轮卡 ~5 分钟(根因已实测) + compass daemon/MCP 断连

来源: nautilus-v5 会话 2026-09-06 · 用户指示"这个问题转给 compass 对话框处理"。
两个并列问题,均已带实测证据。

## 症状
1. 每轮回答结束 UI 显示 `running stop hooks… 2/3 · 4m51s`,每轮都卡约 5 分钟
2. 本会话 nautilus-compass 与 nautilus-compass-cloud 两个 MCP 均 "Connection closed"
3. UserPromptSubmit hook 报 `BGE daemon DOWN`(召回退化为 metadata 列表)

## 实测证据(2026-09-06,nautilus-v5 会话)

三个 Stop hook(~/.claude/settings.json → hooks.Stop),逐个计时:

| # | 脚本 | 实测 | 判定 |
|---|------|------|------|
| 1 | `~/.claude/plugins/nautilus-compass/stop_hook.py` | 5.5s | 正常 |
| 2 | `Projects/nautilus-compass/tools/fuel_intake.py` | 5.9s | 正常 |
| 3 | `Projects/nautilus-compass/tools/memory_git_keeper.py` | **外推 314s** | **根因** |

keeper 证据链:`~/.claude/projects` 下 **1513 个 memory 目录**(每目录一个独立 git 仓,全部含 .git 和 md),
keeper 每轮对每个仓跑 `git add -A` + `git diff --cached --quiet`,抽样 15 目录实测 3.1s → 0.21s/目录
→ 1513 × 0.21s ≈ 314s,与 UI 观测的 ~5 分钟吻合。纯本地 git 操作,与云连接无关。

daemon 证据:netstat 无 :9876 LISTEN,curl 9876 无响应(写单时复核一次,若已复活则只剩问题 1)。

## 用户归因备注
用户初步归因"compass cloud 云端连接失败"。实测显示:5 分钟卡顿与云无关(keeper 纯本地),
云/MCP 断连是并列的第二个真问题。两者都要修,不要合并归因。

## 修复建议(compass 会话裁量)
1. **keeper 性能**(`tools/memory_git_keeper.py`,本仓内改+commit):
   - 加 mtime 过滤:只碰最近 7 天有文件变动的 memory 目录,死目录(1513 中的绝大多数)跳过
   - 备选:BASE 级合并单仓,每轮一次 git 提交(回滚粒度 per-file 仍可)
   - `~/.claude/settings.json` 给该 hook 显式 `"timeout": 60` 兜底
   - 预期:5min → 数秒
2. **daemon/MCP 复活**:
   - 标准拉法:`nohup python ~/.claude/plugins/nautilus-compass/daemon.py > /tmp/compass_daemon.log 2>&1 &`
   - 复核 MCP "Connection closed" 是 daemon 死的伴生还是独立故障
   - ⚠️ cloud 侧 9/5 停操作令(cloud-ops-halt-20260905)仍有效:cloud MCP 断连可诊断、不可对 cloud 服务器做操作,动 cloud 前必须问用户

## 完成判据(独立验证,不是自报)
- 新会话一轮回答结束 stop hooks 总耗时 <10s
- UserPromptSubmit 出现真召回块(`BGE-bge-m3 · daemon · query:` 字样)
- MCP 工具可调(recall/drift_check 等返回 200)
