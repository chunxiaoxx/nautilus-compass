---
name: orgfuel-ORGD-afe3262749d13ec6-76a67f2916
description: "[### 口播+分镜逐段(总 ~82s)] | 时间 | 口播(逐句) | 画面 | |---|---|---| | 0"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-afe3262749d13ec6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 口播+分镜逐段(总 ~82s)] | 时间 | 口播(逐句) | 画面 |
|---|---|---|
| 0-4s | 你的 AI 助手,每次开个新对话,就把你忘了。 | 黑屏白字大卡「agent 记忆层」→终端 |
| 4-14s | 我们开源了 nautilus-compass。在公开基准 LongMemEval-S 全部 500 题上,检索三项全面超过赛道头部 mem0:P@1 0.890 比 0.774,高出 11.6 个点。 | table_headtohead_zh.png 全表,0.890/领先列绿色高亮 |
| 14-26s | 核心赌注一句话:写入时不调大模型。原文原样存、本地嵌入,零抽取、零上云、零写入成本。智能全在读侧——分型路由、混合检索、日期锚定。 | demo:write 1/2/3 三条,尾注 `0 LLM calls · $0` 特写 |
| 26-42s | 接入三条命令。写入三条不同会话的记忆:遛狗、学 Rust、周一例会——每条写入免费且无损。 | 真终端跑 `python tools/demo_d1.py write 1/2/3` |
| 42-54s | 然后提问:用户周二早上干什么?它跨会话命中正确记忆。反过来,问一个记忆空间里没有的,它老实答 NO ANSWER——答案来自记忆层,不是模型瞎编。 | `ask`(命中 Momo 遛狗)→`control`(NO ANSWER)两段对照 |
| 54-68s | 还有动作前护栏:drift 检测。同库两条查询——危险命令立刻报警,正常改动安静通过。这套失败模式锚点,是 130 天、771 次提交里攒出来的。 | `drift` 两行红绿对照(DANGEROUS→ALERT ✅ / NORMAL→no alert) |
| 68-82s | 全部脚本开源,复现成本约 3.
