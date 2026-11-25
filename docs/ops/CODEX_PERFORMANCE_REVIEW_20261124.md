# Codex 对话性能与可靠性复盘（2026-11-24）

## 结论

本次卡顿由多条慢路径叠加造成。主要因素是曾经观测到的全局 `gpt-6.2-sol + max` 慢档、长线程和重复 duty/smoke 会话、每条 Codex 消息触发一次 Compass 全量语义召回，以及 Compass 只读 hook 使用了过期的组织目录投影。当前复读的全局配置为 `gpt-6.1-sol + medium`，Compass 项目单独固定为 `gpt-6.2-sol + medium`。

这几项会同时拉长等待时间，并把历史状态放进当前判断，增加“服务已恢复却被旧记忆判成故障”的误判概率。

## 已实测修复

- 全局 Codex 推理档位当前复读为 `medium`。全局模型名可能被桌面界面写回，因此主线以项目级配置为准。
- Compass 项目固定为 `gpt-6.2-sol + medium`，复杂任务仍可在新任务中显式升档。
- Codex 调用 Compass 自动召回改为轻量路径。需要历史时由任务按需调用 MCP `recall`。
- Codex SessionStart 的 daemon 探活不再等待冷启动轮询。健康时立即返回，未健康时后台启动完整守卫。
- 只读 hook 的 catalog projection 已更新为当前目录 SHA256 `36ac4fb33506919b3270e0745b26eb9a135c36568a77edeff946db1c0aad1a83`。
- 归档重复的 headless duty、smoke test 和已失败 Agent 线程，历史仍保留可恢复。

## 复测坐标

- 本地 9B：`http://127.0.0.1:11435/health` 返回 `status=ok`，模型为 `Qwen3.5-9B-4bit`。
- 本地启动守卫：`local_llm_start.sh --check-only` 返回 0。
- Compass MCP 召回：本轮调用成功，返回 project-scoped recall。
- Compass 只读 SessionStart hook：约 0.03 秒。
- Compass 只读 UserPromptSubmit hook：约 0.19 秒。
- Codex 轻量 UserPromptSubmit hook：约 0.01 秒。
- Codex 全量召回对照：约 1.22 秒，保留为显式调试路径。
- Codex 当前最近列表保留主线 Compass、V5、Platform、Flywheel 和日报，重复 duty/smoke 已归档约 700 条。

## 边界

- 已打开的旧线程不会被改写。新一轮读取项目配置时才使用 `medium`，已失败的 `minimal` 线程保留为历史并已归档。
- 没有删除会话，没有改变平台判据，也没有发送外部消息。
- 系统级 hook、Codex 全局配置和本地启动脚本位于仓库外。它们已在 `~/.cache/compass_codex_optimization/20261124/` 留有修改前备份。
- 没有重启 Mac，因此 NFS 断开后经过完整重启的自动恢复仍未验收。

## 下一步

继续观察新会话的首条响应时间、`catalog changed` 是否再出现、9B 是否保持本地调用。只有出现新的实测回归，才继续修改 hook 或模型配置。

## 2026-11-25 现场复核

- [实测] 当前 `~/.codex` 约 7.7G，`sessions` 约 3.1G，`thread_history_1.sqlite` 约 862MiB。旧 Compass 主线程 `01a1ea00-9c51-7bb0-92d1-2d79b4947675` 累计 tokens 约 1.13B，对应 rollout 约 94MiB，检测到约 249 个 compact 标记，Codex 列表状态为 `notLoaded`。该线程已通过 Codex app 工具归档，历史仍保留。
- [实测] 最近 Compass 线程 `01a211b2-02f2-70d0-8574-83d2dcb98a64` 的 app-server 日志仍记录 `gpt-6.2-sol` 与 `reasoning_effort=max`。仓库 `.codex/config.toml` 已写入 `medium`，但桌面 ChatGPT/Codex 进程自 11 月 24 日 20:12 启动，早于配置文件 20:59 的修改时间，因此运行中的 app-server 尚未重新加载该配置。
- [实测] 当前 Compass、V5、core 和 Flywheel 各有活动线程，共用一个 Codex app-server。进程中还存在 32 并发的远端 exec-server 和 5 个 Compass `mcp_server.py` 实例。
- [实测] 数据盘可用空间约 19GiB，使用率 96%，swap 已使用约 6.36GiB。系统中发现 10 个启动时间为 4–11 小时前的 `find /` 全盘扫描，父进程属于 V5 singleton。已对这些明确的扫描/管线 PID 发送终止信号，部分进程处于不可中断 I/O 状态，等待文件系统调用返回后才能消失。
- [实测] Compass SessionStart 与 UserPromptSubmit hook 当前单次约 0.04 秒，轻量 hook 路径不是本轮卡顿主因。

## 现场复核后的边界

- [推断] 当前新会话仍慢的首要原因是桌面 app-server 没有重载 `medium`，每个线程仍以 `max` 运行，并叠加超大历史数据库、多个活动线程和系统 swap 压力。
- [不可验] 在不重启桌面 app-server、释放文件系统阻塞和降低历史数据库压力前，无法确认新配置是否能改善首条响应时间。
