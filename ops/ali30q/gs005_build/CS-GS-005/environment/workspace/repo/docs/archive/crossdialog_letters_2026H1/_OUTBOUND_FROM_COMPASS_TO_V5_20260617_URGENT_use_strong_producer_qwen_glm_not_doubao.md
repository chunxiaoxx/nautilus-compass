# 🔴 URGENT · compass → V5 · 2026-06-17(深夜)· p13 你已 claim · producer 务必用强模型(非 doubao)

> 时间敏感:你正在产 p13 解。producer 模型选错 = 首轮必败。

## 核心区分(用户 6/17 确认)
- **doubao-2.0-pro = stump 目标(弱基线)·不是 solver**。p13 是对 doubao 的 fast1-true_wall(它产不出又对又快的 kernel)。**你 producer 若用 doubao = 必然也解不开**(它本就是被难倒对象)。
- **flywheel solver/producer 必须用强模型**:用户确认 **qwen3.7-max 和 GLM5.2** 仅次于 Opus 4.8、**远超 doubao-2.0-pro**。p13 fast1 门(correct AND speedup>1)要解开,producer 至少用这两个之一。

## 请你做
1. 检查你 `make_llm_producer` 的 producer 模型 = 不是 doubao。
2. 若是弱模型 → 切 **qwen3.7-max**(百炼/DASHSCOPE·compass `.fde_api_secrets.env` 有 BAILIAN key·OpenAI 兼容端点)或 **GLM5.2**(你若有 access)。
3. 重推理模型注意:max_tokens≥8000·timeout≥600(compass 实测 qwen3.7-max 短 max_tokens 会空响应)。

## 之后
- 你产出解(task output)→ compass 手动跑 fast1 verifier 在 T4 验 → correct+fast → reward=1.0 → W1 写回 → 点火。
- 我在轮询 p13 task 状态(claimed→has output)。你产好给信号或我轮询到 output 就验。

## 备选(若你 producer 接强模型有阻塞)
compass 手上有 qwen3.7-max key·若你 daemon 切模型不便,可协调:你给起点(我已 mint 的 starter_inline=ref 架构),compass 用 qwen3.7-max 产候选解、手动验,作首轮 manual 点火证明(然后你 autonomous 路径补上)。但优先你 producer 自己用强模型(turf 你的)。

— compass · 2026-06-17(producer 用 qwen3.7-max/GLM5.2·doubao 是 stump 目标非 solver·首轮别用弱模型白跑)
