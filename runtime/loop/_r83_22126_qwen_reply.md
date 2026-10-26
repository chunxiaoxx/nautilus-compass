回执 #22126（qwen 复测启动令）。compass 不空跑、不冒充四题齐发。

[实测 16:44]
1. `command -v bl` 仍落空。旧渠道 `qwen3.8max` protocol=bailian 走 bl CLI，Mac 未装——额度加满不能解除此阻塞（与 #21917 同因）。
2. 渠道表已有替代线 `qwen3.8max-bl`（中转站 `bl-qwen3.8-max`，`models_channels.json` 标 verified-20261026）。relay `/v1/models` 200 且目录含 `bl-qwen3.8-max`。本轮按此线发跑，不装 bl。
3. 题面就绪：CS-001 / CS-003 / CS-008 有 `task.toml`。**CS-004R 目录不存在**（items 仅 CS-004）——不编造发跑，请 v5 给 CS-004R 坐标或改指 CS-004。
4. 既有 `qwen3.8max-bl` 读数（score 非空才算）：
   - CS-001：run0–3 = 1.0 / 1.0 / 0.8966 / 0.8966（四轮齐，幂等跳过）
   - CS-003：run1=1.0 / run2=0.6667 / run3=1.0；**run0 score=null，本轮重跑**
   - CS-008：仅 run0=0.913；**run1–3 本轮补跑**
5. 发跑后首轮读数随到随报；判分入总线候跑完。deadline 18:39 内能保证启动与缺口清单，四题×4 全齐取决于 CS-004R 是否到位 + CS-008 三轮耗时。

另报（矩阵红线，同步函 v5）：CS-003 × glm5.3 × run0 于 15:58 / 16:15 / 16:33 三轮同因 JSON parse fail（content empty / substring not found）——**满 3 连同因，已停该组合空转**，不报假分。
