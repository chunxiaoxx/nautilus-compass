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
