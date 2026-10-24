# CS-010 贯通演练战报(2026-10-24 深夜收官)

## 目标达成(平台 21222 令)
✅ S2→S3→S4→S5 全链端到端贯通——首个完整判分读数:
  CS-010 × opus5.5 × run1:score 0.0 / applied 2 / 126.9s / 零错
  run2 复验:score 0.0(两连一致)
✅ **G1 区分度有效信号:opus 两轮 0 分**(TB-01 traceback 帧引用陷阱,opus 推理到根因但未修对)

## 断点全账(8 个,演练核心产出)
| # | 断点 | 处置 |
|---|---|---|
| 1 | 中转站全宕(glm/k3/gpt 500) | 候恢复,跑批器自适应 |
| 2 | RELAY key "缺失"误判 | 实存 .env,更正 |
| 3 | .env 加载路径机制 | 踩通 |
| 4 | (1 的根因确认) | 同 1 |
| 5 | 百炼 key 缺+流挂起 20min | 候 v5 供 key(21241) |
| 6 | model_solve out_detail bug | 两刀修(v2 函数级) |
| 7 | qwen 渠道阻塞 | 同 5 |
| 8 | 判分环境 pytest 缺 | venv-judge 建成 |
| +9 | code80 409 限流冷却 | 循环自动补 run0/3 |

## 循环接管(人工退场)
- launchd 每小时轮(幂等:仅 score!=None 算完成,409/500 自动重考)
- 中转站恢复→自动扩 5 渠道;百炼 key 到→qwen 补
- CS-011~014 就绪(笔记本线交付)→自动进考
- B 批 5 题矩阵死线 10/30 18:00

## 关键修复物(入 v5 仓待审)
- tools/model_solve.py: out_detail 函数级初始化(compass 修)
- tools/models_channels.json: glm5.3-anthropic 应急通道
- codesense/.venv-judge: 判分专用 venv(pytest 9.1.1)
