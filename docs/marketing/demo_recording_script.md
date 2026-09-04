# Demo 录屏脚本 · D1 跨会话记忆(60-90s,Reddit 帖嵌入用)

> 目标:让 r/LocalLLaMA 读者在 60 秒内"看见"跨会话记忆+无损写入的价值。
> 形态:终端录屏(深色主题·字号 ≥18pt·1080p·帧率 ≥30fps),可直接嵌入 Reddit(转 GIF 或 mp4 链接)。
> 🔴 录制前先用假数据彩排一遍全流程(调用形态已在生产验证过,本地演示以 daemon 实际工具名为准)。

---

## 分镜脚本(总 75s)

| 时间 | 画面 | 动作 | 字幕/旁白要点 |
|---|---|---|---|
| 0-8s | 标题卡(黑底白字) | 静止 | "nautilus-compass · agent memory that survives sessions · zero LLM at write time" |
| 8-15s | 终端 | 展示 daemon 状态/版本一行 | "fully local · your data never leaves the machine" |
| 15-35s | 终端 | **会话 1/2/3 依次写入**:三条 ingest 命令,每条一句不同会话里的用户事实(见下方素材) | "three separate sessions · writes are free: no extraction, no LLM, verbatim" |
| 35-55s | 终端 | **新会话提问**:一条 recall 命令,query 是只有跨会话才能答的问题 → 展示召回命中三条中的两条 | "one question, three sessions · routed retrieval finds the right granularity" |
| 55-70s | 终端 | **对照组**:空白空间(全新 project)跑同一 query → 空/无命中 | "control: empty memory, same query — the difference is the memory layer" |
| 70-75s | 收尾卡 | 静止 | "MIT(Modified)· github.com/chunxiaoxx/nautilus-compass · hosted beta: compass.nautilus.social" |

## 会话素材(写入内容设计,问题必须"只能跨会话回答")

- session-1:`用户说他周二早上遛狗,狗叫 Momo`
- session-2:`用户提到他在学 Rust,目标是用它重写公司的数据处理管线`
- session-3:`用户抱怨每周一例会总被临时取消`
- **跨会话问题**:`What does the user do on Tuesday mornings?`(答案要素只在 session-1)
- 对照命中预期:recall 返回 session-1 片段(含 Momo/周二);对照组返回空

## 技术备注

1. 两条路径任选:**a) 本地 daemon**(更能体现 local-first,README 三条命令场景);**b) hosted 端点**(调用形态已验证:curl + Bearer token + JSON-RPC tools/call,参照 `probes.py` 的 `_rpc` 写法)。**推荐 a**,与帖子叙事一致。
2. 写入工具:hosted 为 `ingest_obs`;本地 daemon 以 `tools/list` 实际输出为准——**彩排时先跑 tools/list 确认工具名再定脚本**。
3. 终端:字号 18pt+;提示符短(`$`);录屏只框终端区域;光标移动别太快。
4. 每条命令之间留 2-3 秒停顿,输出完整可见后再下一条。
5. 录完检查:字幕时间轴/无个人路径泄露(home 目录用户名打码)/对照组确实为空。
6. 兜底:若本地演示彩排不顺,降级用 hosted 路径录(生产已四绿+压测过)。
