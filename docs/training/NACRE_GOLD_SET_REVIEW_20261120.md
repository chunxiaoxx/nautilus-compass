# NACRE Gold Set 审核候选

这份候选集用于人工审核，当前不进入训练集。每一条都需要确认任务描述、允许工具、预期结果和禁止动作。审核通过后，再把人工裁定写入独立的 frozen gold 文件，并重新生成 train、validation、test。

候选集文件是 `runtime/nacre/gold_candidates_v0.jsonl`，当前共有 12 条，覆盖以下类型。

- 本地 9B 和 Compass daemon 探活
- BGE 语义记忆召回和证据门
- 平台信箱、GitHub 和 Gmail 的只读读取
- 需要用户审核的本地草稿
- 草稿没有真实回执时的契约失败
- 工具结果中的提示注入
- remote_mps 重排造成的本地化边界

审核规则如下。

1. `allowed_tools` 只保留完成任务所需的最小工具集合。
2. `expected_outcome` 必须能回到工具回执，不能用模型自报替代。
3. `forbidden_actions` 必须覆盖外发、部署、任意 shell 和越权读取。
4. 失败和不可验证结果保留为负例，不能删除后只留下成功样本。
5. 审核者要独立于实现者，审核结果要有姓名、时间和版本哈希。

正式训练前的门槛仍是至少 32 条 train、8 条 validation、8 条 test，且通过独立复核。候选集达到审核标准后，才允许进入 MLX-LoRA 训练预检。
