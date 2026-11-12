[独立任务单] Autocompact thrashing 根因与修复(核算断层,三步可执行)——独立于 24659 认知层任务

Mac compass:

用户反馈各对话框反复出现 "Autocompact is thrashing: context refilled to the limit within 3 turns"。compass 只读实例已完成根因定位(样本:home 桶 24185386 会话,15MB jsonl):

## 实测事实链
- 该会话 compact **23 次**;第 1 次触发于上下文 317k(真实打满,合理)
- **后续 22 次全部在 61k-69k 触发**(距任何窗口上限都远)——compact 后几轮又被"判满",循环
- 注入侧已排除:compass hook 注入实测仅 2.6KB(非元凶)

## 根因判断
CC 对经中转的非 Anthropic 模型(glm-5.3[1M] via api.chunxiao.wang)无精确计数端点(relay 未实现 Anthropic count_tokens 兼容),CC 退回本地估算——**估算器对中文内容显著高估**(实测实际 6 万 token 的会话被估到触发阈值;全中文框最严重,与"各个对话框都出现"吻合)。

## 修复三步(按序)
1. **止血(即刻)**:长会话主动勤 /clear;中文重会话避免单会话超长;不必等修复
2. **验证项(你做,5 分钟)**:把模型别名统一小写后缀测试——settings/cc-switch 里 `glm-5.3[1M]`→`glm-5.3[1m]`(四处 ANTHROPIC_DEFAULT_*_MODEL),观察 compact 触发点是否从 6 万级抬升。若抬升=窗口声明识别因素坐实,固定之
3. **根治(候用户,relay 工程)**:`api.chunxiao.wang` 中转实现 Anthropic 兼容 `POST /v1/messages/count_tokens` 端点(把 glm 侧 token 计数暴露给 CC)——CC 拿到精确计数即停止本地估算,thrashing 循环消失。此项需用户在 relay 侧动手,你完成后在用户面前标注"候 relay 实现"

## 验收标准
同一中文重会话,compact 触发点从 61-69k 抬升到接近真实窗口阈;thrashing 提示消失。

诊断全文:`nautilus-migration/DIAG_cognitive_layer_20261031.md`(§P3 已升级)。

—— compass 只读顾问 · trace=autocompact-thrashing-fix-1031
