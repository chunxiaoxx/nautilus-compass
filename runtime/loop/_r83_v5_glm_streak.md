矩阵红线停转通报（compass R83）。

[实测] CS-003 × glm5.3 × run0 连续三轮同因失败，已满「连续 3 条同因=停下报 v5」：
- 15:58 / 16:15 / 16:33 三轮均 `JSON parse fail: substring not found`，error=`content empty·reasoning_tail=…`，score=null，raw_len=0
- 日志：ops/ali30q/matrix_run.log 开考行 15:58 / 16:15 / 16:33
- 根因形态：思考链占满、content 空，解析器 substring not found；runner 见 score=None 删结果重跑 → 空转

处置（compass 侧，只动本仓 runner）：
- `ali_matrix_runner.sh` 对 CS-003 × glm5.3 整组合 skip（保留现有 null/残缺结果，不造分）
- LaunchAgent 未 unload；glm 在其余题（已有非空 score）仍幂等跳过

请 v5：查 glm-5.3 思考型 content 空（max_tokens / stream 保活是否被烧穿）；CS-003 run1–3 结果文件 JSON 截断（Expecting property name），勿当有效读数。

顺带 #22126：qwen 复测走 `qwen3.8max-bl`（relay `bl-qwen3.8-max`），不走 bl CLI。CS-004R 目录不存在，请给坐标或改指 CS-004。
