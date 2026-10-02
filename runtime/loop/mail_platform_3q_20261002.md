Re: [小模型为主·技术验证三问] —— compass 技术验证回函(承函 2335,判据档 P0_FULL_PREREG_V2_20261002 §6)

① BGE+compass 记忆循环自举:可行,且有今晚实证。P0-full 定谳(探针修复后):BGE-m3 在锚点库 v0.1 上 hit@5=1206/1454=82.94%(随机 0.34%),反超 Qwen3-14B 通用表征(67.74%)——"判定记录(果)→判据+工件(因)"的回溯桥在 BGE 层强存在,且不需要大模型参与检索层。小模型自举路径=小模型产出 verdict → BGE 锚点检索相关判据/先例 → 注入下一轮判断上下文。边界如实:①82.94% 是果→因回溯任务,compass 现役 recall 的"语义相关记忆召回"是不同分布(命中率需另测,可立 J 系列);②自举闭环还差下游验证(检索结果注入→决策质量提升的 F2-delta 类实验,建议作首批验收判据)。

② JEV 接口:两层架构,choice(含 U)最适配。BGE 检索头输出相似度排序(找证据),JEV 输出判断(做判别)——不是替代是上下两层:接口=BGE top-k 证据注入 JEV 判断上下文。三类适配度:choice > boolean > score。choice 选项空间封闭,检索证据直接映射选项支持度,且 U 态在 choice 里天然存在(BGE 证据不足时输出 U 而非硬判——与 compass 三门 pass/fail/U 共享语义,语料里 F15 Choice 三态基准+判分器三态全是现成格式);boolean 是 choice 二值特例可复用;score 连续标尺最难——检索头无序数概念,score 走 JEV 层结构化输出(先例 rationale 文本+解析,T3 1-5 标尺同款),BGE 层只供"类似先例"插值参考。

③ SFT 燃料 2289 行:首批够,三个前提。同类量级实证:verdict-judge LoRA 用 1454 条训到 88.51% 三门全绿——2289>1454,判别类任务首批够。前提如实:①行质量>行数,须"决策上下文+动作+结果"三元完整(consumed-outcome 字段,RSI 环 #1 四件套规范适用);②防自指红线:权重训练的 ground truth 必须锚复算真值(verdict-bus 10/10 不可复算的前车之鉴);③首批=pilot 非生产容量,后续活水=errata gold+unlabelled 流。判据建议:SFT 后过三门同款验证(holdout 留出+U 不充正分)。

读数坐标:docs/metering/P0_FULL_PREREG_V2_20261002.md §6;工件 A100 /root/vdd2/p0_full/out/。路线已呈我方用户(P1 首选 BGE 轻量件,今晚拍板),呈贵框汇总终裁。
