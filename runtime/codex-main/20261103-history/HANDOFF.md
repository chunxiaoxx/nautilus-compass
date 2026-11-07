# Compass 过去、现在、未来梳理交接

task_id：`COMPASS-HISTORY-PRESENT-FUTURE-20261103`。Owner：Compass 本仓主会话 / Codex。

验收目标：将历史演变、当前用户确认的职责、当前运行入口、已有实物、历史负结果与未来实验门槛串成一条可追溯主线；历史报告、源码、实测和不可验事项分层。主交付：[COMPASS_PAST_PRESENT_FUTURE_20261103.md](../../../docs/soul/COMPASS_PAST_PRESENT_FUTURE_20261103.md)。

已完成的实质增量：

1. 定位最早可达 git 提交（4/27 zenmind-mem），串起 5/31 可靠性定位、7–8 月记忆实验、9 月独立验证、10/8 三位一体与创新模型、10/19 自举线否决、11/2 当前职责。
2. bootstrap、本地 daemon/BGE、连接器召回、公网 MCP initialize/tools/list/recall 均读通，命中源已回读。只取相关信息，不 ack、不发送、不推进旧任务。
3. 查明发布入口差异：主包 3.3.0、jev-trust 0.2.1、assay-verify 0.1.0；旧盘点的独立包名 nautilus-compass-assay 返回 404。
4. 查明判官 88.51% 在现存原 JSON 中名为 binary_acc，旧“三态”口径不直接沿用。模型工件存在，但没有本轮在线推理验收。
5. 按行级 CSV 独立重算 E-NACRE-1：A 256/292，B 149/292，差 −36.6438pp；每臂 291 唯一 qid，重复行保留。复算仅覆盖存档标签下的统计。
6. 7 个旧输入 SHA 未变；本地 anchor_v01 数据/P0-full 精确路径仍缺；保留已收束的远端认证缺口，未扩搜或重试 SSH。
7. 纠正生命周期旧状态：当前源码已有 forget_at 过滤与 tier 加权，不能只按 11/1“无执行器”定性；当前开关与任务效果仍待专项验收。

证据坐标：`SOURCES.json`（40 个源）、`BOOTSTRAP_READBACK.json`、`RUNTIME_PROBES.json`、`PUBLIC_MCP.json`、`PUBLIC_RECALL.json`、`PYPI_READBACK.json`、`ENACRE1_RECOMPUTE.json`、`INPUT_READBACK.json`。交付核对见 `DELIVERY_CHECK.json`。

剩余问题：

- 当前消费者的任务收益、持续性能和外部采用/付款/验收未做全量审计。
- 新架构 anchor/数组与逐行真值链未补齐；旧 A100 SSH 认证失败不能推出远端文件不存在。
- C 有效秩到 C_m 映射、基准集合、准确率阈值等文档差异尚未绑定同一执行 manifest；全链成本、消融与错误锚点回退未验收。
- 当前训练资源、复盘条件与完整点火条件未核；历史条件许可与后续限制均保留。
- FRAME、远端 registry、旧路线图与当前职责存在日期差；报告为派生快照，不建立第二份业务台账。

下一动作：沿 11/2 network-stage 交接，只处理既有入口认证与旧 out 小索引；随后按原清单核 SHA/行序/fold/label/数组。记忆侧先做真实任务使用链验证；模型侧在执行 manifest 与度量可运行后再做完整对照实验。

写入范围：本任务目录与一份 docs/soul 派生报告。仓内已有源码、配置、记忆与状态改动保留；本轮未启动模型训练、恢复历史循环、重启、部署、外发或提交 git。只读请求可能产生服务自身访问日志。工作期间观察到外部提交推进 HEAD，前后值与来源漂移检查记入 DELIVERY_CHECK。

## 2026-11-03 R2 追加交接

任务 `COMPASS-HISTORY-PRESENT-FUTURE-20261103-R2` 已沿既有报告补充关键证据，核对起点为纽约时间 11:08。主文的“2026-11-03 追加核对”包含演变决策、实现与固定提交、成果层级、失败经验、负责人/依赖及下一步完成判据。新增证据在 [ADDENDUM_20261103_R2_EVIDENCE.json](ADDENDUM_20261103_R2_EVIDENCE.json)。

- 回读 10 条原始用户记录，核实条件点火、SSI 对照、A+B 准备、停止值守同时继续模型准备，以及原生能力和主线三点归属。当前职责依据 canonical catalog。
- 找回记忆效用原始基线与 9/2 复测，固定两次提交，核出 F2 从 0/3 到 3/3，F1 仍失败，F3 不变。结果分层和小样本边界已补入主文。
- 为记忆、assay/JEV、P0 代码补文件级提交与工作区 SHA。既有理论、判官报告、路由 CSV 与 7 个数据输入的连续性核对通过。
- 回读当前 CU04 0.2.1 的完整 5+5 矩阵并重算，Qwen/Opus 均分均为 1.0，Qwen 数值难度门 FAIL。旧“各一次”回复对应早先快照。CU 作为支持任务留在原平台版本链。

主线未决事项集中在真实任务记忆收益、anchor/数组与真值链、C/V 度量和冻结执行 manifest、当前资源与 M1 复盘、assay/JEV 消费者闭环。各项负责人和完成判据已写入主文表格。

本轮采用按时间追加的方式保存原报告与交接前缀。证据文件中的 `delivery_validation` 记录前缀保全、来源漂移、结果复算和链接核对。历史回读是有边界抽样，10/19 定谳仍按原勘误记录层级处理，完整新架构与当前业务收益待后续验收。
