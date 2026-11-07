本轮已做完限定的物料定位，尚未找回 anchor_v01 数据和 P0-full 数组。新增证据是：两份 NAS 项目备份也只有同一份 manifest；原始 A100 工件有明确坐标，但当前只读 SSH 失败。本轮到此停止，等待协调框安排下一步。

任务：`COMPASS-MAIN-20261102-ARTIFACT-LOCATE-01`。Owner：Compass 本仓长期主会话 / Codex，负责长期记忆、assay/jev、压缩×验证与因果倒置模型。本框不是历史 Ali 支持会话。仓库 HEAD：`e6fe8d55c147bff90b1b90077280ebd2d4c80f01`，本轮未改变。

验收目标：最多 5 个有来源候选，只查现成产物；找到后核 SHA、ID、fold、label 和原 manifest，未找到则保留有边界的缺口。详细记录见 [STARTUP_ACCEPTANCE.json](STARTUP_ACCEPTANCE.json)、[CANDIDATES.json](CANDIDATES.json) 和 [SOURCE_CHECKS.json](SOURCE_CHECKS.json)。本轮完成了定位与压缩交接，数据恢复仍未完成。

**新增实测与边界**

候选已经收束，不再继续扩搜。NAS 前缀为 `/Users/chunxiao.wang/mnt/nas-work`。

| 候选 | 有依据的坐标 | 本轮读数 |
|---|---|---|
| 1 | 本仓 `runtime/verdict_corpus`、`runtime/p0_full` | manifest 可读；anchor_v01.jsonl 与 P0-full 精确目录未找到 |
| 2 | NAS `backup-projects/latest/nautilus-compass` | 同上；backup.log 的完成日期是 10/19，不能把 latest 当今天快照 |
| 3 | NAS `backup-projects/2026-10-19/nautilus-compass` | 同上；与本机及 latest 的 manifest 字节一致，不是三次独立实验 |
| 4 | NAS `migrated-dataroot/nautilus_bigfile_backup` | 已有 18 行 SHA 清单无目标项，精确路径也未找到；清单的完整覆盖范围未核 |
| 5 | 旧 A100 `/root/vdd2/p0_full/out` | 来源为 `p0-full-verdict-20261002.md:22`；单次只读 SSH 退出 255，没有读到远端文件 |

[实测] 三份 anchor_v01 manifest 的 SHA256 均为 `04cc24cb777fef842b0387b9f0fc8b805315a61bb0fbadd06760b3a914b40d11`，其中记载 n=1454、原数据 SHA16=`e710a70105df50e7`。这证明清单被保留，不能证明数据可读或标签正确。

[实测] 7 个既有输入的原始字节 SHA 与前轮一致，详见 [INPUT_VERSION_CHECK.json](INPUT_VERSION_CHECK.json)。因此没有重复 1454 拆分、分组、标签和 REG100 整套验证；旧结论只沿用到这些相同版本，不补做语义金标背书。

[实测] `tools/p0_full_extract.py:81-99` 的 metadata 写 n、ID 顺序短哈希、数组形状等，没有数组 SHA、完整 ID 列表或逐行 fold/label。`tools/anchor_build_v01.py:131-153` 才定义 anchor_id、fold、truth_label、u_flag 等字段。下轮找回 meta 不能直接判为恢复完成，必须绑定原 anchor 行序。历史文档给出的 ids_sha16 是 `062ae3cd6b529916`，q14 形状记载为 1454×5120；这两项目前仍是历史参照，未用现存数组复验。

[实测] 当前 Compass MCP 做了一次本仓命名空间 recall，top_k=3，命中并回读 `day-log-20261002-gtaras7-erratum.md`，源 SHA256=`5caaf37611d15bdbe08bcf110d3c45a12728b7cbbe2c4bd0a62c0caad426f33d`。只读了相关命中，未展开其他无关命中。请求与来源见 [MCP_RECALL.json](MCP_RECALL.json)。bootstrap 请求失败，信箱和运行身份未核；未 ack、未回函、未 ingest。

[推断] 目前缺口跨越本机与两份备份，值得优先回到旧产出目录核索引。这仍不证明其他备份没有文件，也不构成永久冻结理由。

**下一轮可执行清单，待协调后再做**

1. 先由协调框安排可达的既有只读入口，只针对候选 5 读 `/root/vdd2/p0_full/out` 的现成文件索引；优先 `meta_q14.json`、对应 effect/cause 数组、已有 turbo/BGE 产物和原始评测 manifest。anchor_v01 的实际远端路径须由索引确认；`/root/vdd2/p0_full/anchor_v01.jsonl` 只是脚本默认名推导，不能冒充原路径。本轮没有理由增加第六个候选或重提特征。
2. 找回 anchor 后，先元数据和敏感检测；分别记原始字节 SHA、LF 规范化 SHA。若要与旧 Windows SHA 比对，单列 CRLF 表示，保留末尾换行差异，不悄悄改源文件。比原 manifest SHA16、唯一 ID/行序、fold、truth_label、u_flag，与当前未变的 split/anchor_v0 对齐。只校验找回的新物料，不重跑整套旧验证，不输出 effect/cause 正文。
3. 用 `hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()[:16]`（ids 为原行序的 anchor_id 列表） 绑定 metadata；比 n、数组头形状和 dtype。数组完整 SHA 与能找到的原始 SHA 分栏记录；旧 metadata 没有原 SHA 时，只能标“本轮新算”，不能写“已与原数组比对一致”。只有形状一致不能证明语义、标签或完整 F1-F4 链通过。
4. 沿现有理论正本寻找已冻结的执行 manifest 和 CPU C/V 结果，先解决三个基准集合及阈值的文档差异：V3 写 CauseNet/BigCause/标准多跳，蓝图建议 verdict/CV/数值；“相对下降 2%”与“±2 个百分点”并列保留，不能自行选更宽口径。有效秩到 C_m 的映射、全链 FLOPs/时延、兜底路径需有可复算实现和原始输出。本轮没有新建理论定义或计算脚本。
5. 同一执行 manifest 要绑定 Baseline、检索头、+SSI、+JEV、纯相似度对照，以及混淆/OOD/错误锚点集和程序判定或人工盲评。检索 hit@5 不能替代整架构效率与错误率验收。500 条重判的 judge_raw 依赖、4 份缺失的官方 LME 导出及独立审计证据仍分开待核；不把 label_origin 字样当逐行金标。

理论正本均已读回，SHA 与前轮一致：`../verification-learning-papers/docs/CV_eta_engineering_spec_v3.md:20-76,119-166`；`training_blueprint_cv_arch_20261001.md:12-55,81-85`；`CV_falsification_core_20261001.md:10-28`；`unified_metrics_charter_20261001.md:25-61`。详细 SHA 在验收 JSON。组织原则仍为“智能＝压缩×验证”；工程 η=C_m/V⁻ 与总量 I_eff=C_t×V⁺ 按现有正本分开，不混报。

历史授权：本轮回读的是现有 `compass-original-decision-readback.json` 的 U02/U05/U06/U12 坐标，没有再读原始会话。U02 的历史条件点火授权保留；其原记录时间为 10/2 16:32（+08），不能沿用旧日志“17:0x”或简单说成全线解冻。本轮未检查当前 GPU/M1，也未把旧授权扩为当前训练授权；缺文件不是永久冻结证据。

敏感边界：迁移项目清单第 5302 行命中凭据格式，仅在 SOURCE_CHECKS 中保留存在性、文件 SHA、行号及行 SHA，未复制值。无原始历史或模型权重被删除。未新起模型、未提特征、未下载、未训练、未重启共享服务、未恢复循环、未分派子代理、未 commit/push/deploy/结算/外发。所有本轮写入都在当前 runtime 目录。
