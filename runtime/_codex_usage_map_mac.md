# Codex 双轨使用映射卡(Windows CLI → Mac CLI+GUI)

> 2026-11-04 compass 审计席写(机制全部实测,GUI 交互细节候你实测后补)
> 位置:`~/.codex/USAGE_MAP_20261104.md` · 正本留档 NAS nautilus-migration/COORD_mac_pending_resolution_20261104.md §4.2

## 已实测机制(排障先读这四条)
1. **CLI 与 GUI 共享同一个 `~/.codex`**:auth(已登录)/会话/索引全通——CLI 里 resume 的会话 GUI 里也能看到,反之亦然。
2. **GUI 侧边栏标题 = `~/.codex/session_index.jsonl` 每行的 `thread_name`**;会话本体 = `~/.codex/sessions/年/月/日/rollout-*.jsonl`。侧边栏找不到旧会话=索引没合并或文件没落地(11/4 导入 T6 修的就是这个)。
3. Codex 桌面版是 **ChatGPT.app 内嵌**(不是独立 Codex.app);CLI 是 `codex`(0.166.0,/opt/homebrew/bin)。
4. 旧版目录(archived_sessions/worktrees 等)新版无对应,别在新界面找。

## 旧 CLI 习惯 → 现在怎么干
| 旧(Windows CLI 0.158) | 现在(Mac) |
|---|---|
| `codex` 起交互会话 | 终端 `codex`(同);或 GUI 新对话 |
| `codex resume` 续旧会话 | 终端 `codex resume`(列表带标题);GUI=侧边栏点标题 |
| `cx` 包装(zshrc 已迁) | 直接可用(终端) |
| 找历史会话 | GUI 侧边栏搜标题;或 `grep thread_name ~/.codex/session_index.jsonl` |
| 看会话正文 | `less ~/.codex/sessions/2026/*/*/rollout-*.jsonl` |

## GUI 待你实测后补(用着顺手就写一行,攒成自己的卡)
- (候补)resume 旧会话的入口/快捷键
- (候补)侧边栏搜索/置顶
- (候补)导出/分享
