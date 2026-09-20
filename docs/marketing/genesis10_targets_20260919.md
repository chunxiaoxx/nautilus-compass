# 创世十家 · 示范性免费复算目标清单(2026-09-19 · P0)

> 打法已改:不是"求人来做",是**做完了给你看**——主动复算其公开声明,带回执登门。
> 硬条件:目标公开发布过可从公开 artifact 复算的声明(基准日志/评测脚本输出在公网)。
> 姿态:回执先行,agree 是给他们的礼物,disagree 私发不公开(公开与否由他们选,
> 我们只承诺:不问就私发,问了才上墙——第一单不树敌)。

| # | 目标 | 可复算声明 | 证据位 | 优先 | 状态 |
|---|---|---|---|---|---|
| 1 | **Aider**(Aider-AI) | SWE-bench/polyglot/refactor 各模型成功率 | Aider-AI/aider-swe-bench / polyglot-benchmark / refactor-benchmark(已验证存在,公开日志) | ★★★ 社区引用率最高,日志最全 | 候选 |
| 2 | OpenHands(All-Hands-AI) | SWE-bench 解决率 | openhands-resolver 仓+发布报告 | ★★★ | 候选 |
| 3 | SWE-agent(princeton-nlp) | SWE-bench 官方数 | 论文附录+复现脚本 | ★★ | 候选 |
| 4 | smolagents(HF) | GAIA 成绩 | 博客+cookbook 产物 | ★★ | 候选 |
| 5 | browser-use | web agent 任务成功率 | 仓库 README 数字+demo | ★ | 需验证证据可复算性 |
| 6 | gpt-engineer | 生成可运行率 | evals 仓 | ★ | 候选 |
| 7-10 | 待补(择标准:中文圈 agent 产品发过跑分者优先——离用户暖渠道近) | | | | 空 |

**执行节奏**:每天 1 家(证据抓取→打包→三门/对应判据复算→出回执→登门评论/邮件)。
首单=Aider(swe-bench 仓日志按模型×题目结构化,天然适合 json_map_equal 类复算)。

## 7-10 位补全(2026-09-21,B 类默认值「创世清单我出」兑现 · 中文圈具身/agent 优先)

| # | 目标 | 可复算声明 | 证据位 | 状态 |
|---|---|---|---|---|
| 7 | **iFlow CLI(心流)** | Terminal-Bench v1(Qwen3-Coder-480A30 / Minimax-M2 双 run) | laude-institute/terminal-bench-leaderboard 仓 20251026_iflow-cli_Qwen3-Coder-480A30 + 20251111_iflow-cli_Minimax-M2(逐 trial results.json **配方 100% 复用**,同 Terminal-Bench #2017 判法) | 🎯 首选 |
| 8 | **Chaterm** | Terminal-Bench v1 多条目(20250911/20251010/20251016) | 同上仓(20251016_Chaterm_claude-4-5-sonnet 等) | 候选(中文圈属性待核) |
| 9 | **camel-agent / apex_agent** | Terminal-Bench v1(gpt-4-1 / claude-4-5) | 同上仓 20251007_camel-agent_gpt-4-1 / 20251019_apex_agent_claude-4-5-sonnet | 候选 |
| 10 | **AGIBOT WORLD 数据集**(智元) | 开源具身数据集完整性/manifest 声明 | AGIBOT_WORLD 公开仓+HF(episode manifest 格式=v0.3 episode kind 实弹候选) | 候选(数据线,对齐方向锚) |

原则不变:agree 礼物/disagree 私发/中文圈优先;#7 与 #2 同判法零新增成本,**优先打**。
