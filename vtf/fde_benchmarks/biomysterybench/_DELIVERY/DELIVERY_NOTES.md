# BioMysteryBench 投递说明(试点批 · 2026-07-17 · 已过买方文档对照审查)

> 试点交付:**3 道题 / 2 模板**,证两条生产线端到端可行 + 逐条对照买方《BioMysteryBench 数据要求【外部】》审查通过。非 500 全量(全量计划见 §四)。
> 🔴 **投递给买方 = 仅 `problems.csv` + `data/*.zip`**。`_INTERNAL_provenance.json`(含答案+溯源)**留内部,勿投递**。

## 一、投递内容

| id | 模板 | 数据 | 隐藏答案(内部) |
|---|---|---|---|
| bmb_vendor_000001 | VCF→变异临床意义 | 3001 变异匿名 VCF(真实 exome 子集·99KB) | PAH \| Phenylketonuria |
| bmb_vendor_000002 | VCF→变异临床意义 | 3001 变异匿名 VCF(真实 exome 子集·99KB) | ATP7B \| Wilson disease |
| bmb_vendor_000003 | 序列→基因/病(序列比对) | 10 条匿名蛋白 FASTA | HEXA \| Tay-Sachs disease |

买方格式 = `problems.csv`(id/question/answer_rubric/allowed_domains/human_solvable)+ `data/<ID>.zip`(纯数据,解压即工作空间)。

## 二、逐条对照买方需求文档(审查通过)

| 买方条款 | 交付符合情况 |
|---|---|
| §2 任务来源:真实**或构建**的生物数据 | ✅ ClinVar 真变异构建 VCF / RefSeq 真蛋白;买方明确接受"构建的" |
| §2 反向推演(非纯查询/描述统计) | ✅ 从匿名证据反推隐藏基因+病/蛋白身份 |
| §2 必须借助外部工具 | ✅ 变异注释/数据库检索/序列比对 |
| §2 唯一答案+列出变体 | ✅ 均唯一,rubric 列别名 |
| §3 ID 与 zip 名匹配 | ✅ |
| §3 不在文件名/列名/元数据/提示词泄露答案 | ✅ 建题期泄露断言(镜像验证器)+ 匿名剥注释;盲解只读 zip 独立解出 |
| §3 问题独立完整英文 | ✅ 英文,**自然简洁一句直问**(对齐样例 qes1"What cancer is found…"风格:无背景铺垫/无工具说明/无格式模板);跨题轮换措辞不模板化;答案格式由 rubric 界定(qes1 亦如此) |
| §3 全对全错 rubric 含标准答案 | ✅ "1.0 or 0.0, no partial credit. The answer is …" |
| §3 allowed_domains ⊆ 14 白名单 | ✅ 均列全 14(对齐 qes1,给模型足够自由度) |
| §4 难度 20-30min / 约 10+ 工具交互 | ✅ VCF 30 变异(需逐个注释+查库,远程盲解 ~60 次交互);序列题 10 次比对/墙钟 1204s |
| §4 唯一答案+等效拼写/别名 | ✅ rubric 明列别名 |
| §4 全有或全无 | ✅ 仅 1.0/0.0 |
| §5 拒收项(难度低/无需工具/泄露/无法加载/答案模糊/不符风格) | ✅ 逐项规避;风格贴买方 qes1(身份/变体反推 + 允许工具) |

**审查发现并已修的 5 处**(见 commit 记录):F1 问题去具体工具产品名 · F2 VCF 变异数 18→3000(真实 exome 子集体量,消"难度过低") · F3 domains 补全 14 · F4/F5 对齐 qes1。

**买方反馈已收(2026-07-17)**:「题目描述有 AI 感和模板化,建议看原 BioMysteryBench 出题格式,自然简单语言、不需背景介绍」→ 已改:三题题干重写为 qes1 风格自然一句直问,去掉全部背景铺垫/工具说明/`GENE|Condition` 格式模板;跨题轮换措辞治模板化;答案格式移入 rubric。验证器同步校准(不再对自然题干误报 no_tool/no_answer_format)。

## 三、验收证据(独立验证,非自报)

- **供应商门** `bmb_validator.py`:合并 3 题 → **0 REJECT / 0 WARN / exit 0**。
- **真解(盲解:只读交付 zip,公共工具链独立解出)**:

| id | 盲解答案 | 唯一性 | 工具交互 | 难度 |
|---|---|---|---|---|
| 000001 | PAH\|Phenylketonuria | 致病唯一=1(本地 ClinVar 全扫 3001 变异复核) | 3001 变异需批量注释+筛选 | 模型侧 20-30min(brute-force 不可行→逼真工作流) |
| 000002 | ATP7B\|Wilson disease | 致病唯一=1(同上) | 同上 | 同上 |
| 000003 | HEXA\|Tay-Sachs disease | 溶酶体酶唯一=1 | 10 次序列比对 | 墙钟 1204s(供应商已知解法) |

- 难度守恒:VCF 答案为 missense,藏在多个良性 missense 干扰里 → 不能靠后果类型蒙,须逐个查库。
- 本地 QC(本地 ClinVar 镜像):#1/#2 各 ~3ms 复核致病唯一=1。

## 四、数据真实性(买方跑 AI 检测的红线)

**全部真实数据,零 AI 凭空造**,每条可溯源(见 `_INTERNAL_provenance.json`):
- VCF 变异 = 真实 ClinVar 记录 + 真实 GRCh38 坐标(`canonical_spdi`),每条有 VCV accession。
- 蛋白序列 = 真实 NCBI RefSeq,每条有 NP_ accession。
- 匿名化 = 剥 rsID/INFO/基因名/致病性/FASTA 头 → 中性标签;答案不出现在任何交付文本/元数据。

## 五、扩到 500 的生产环境(不需要 GPU)

- 重计算全在 NCBI/Ensembl 服务器,本机只 Python;任何阶段零 GPU。
- 生产机 = 1 台普通 CPU 机 + 本地镜像库消限速:本地 ClinVar(已建 SQLite 420万/413MB,查询 ~13583× 提速、结果一致)· 待补本地 VEP cache + SwissProt 比对库。
- 500 唯一性 QC 本地 ~1.5s(远程 16+h)。门槛在策展(~10-12 模板×数据集库)+ QC,不在算力。详见 `../DESIGN_500_scale.md` + `../README.md`。

## 六、给买方的话(建议随交付)

- 2 模板试点批,均过 bmb-infer 前置自检(格式/泄露/唯一/难度),请抽检。
- 全量 500 走"模板 × 真数据集库 × 自动化产-验管线",跨买方 8 类型铺开、反单调批次。
- 交付载体最终可上飞书多维表格 + 网页(本目录为文件形态源)。
