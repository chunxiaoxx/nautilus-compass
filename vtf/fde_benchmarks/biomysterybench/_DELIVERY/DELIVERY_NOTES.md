# BioMysteryBench 投递说明(试点批 · 2026-07-17)

> 试点交付:**3 道题 / 2 模板**,证两条生产线端到端可行 + 过买方验收档。非 500 全量(全量计划见下)。
> 🔴 **投递给买方 = 仅 `problems.csv` + `data/*.zip`**。`_INTERNAL_provenance.json`(含答案+溯源)**留内部,勿投递**。

## 一、投递内容

| id | 模板 | 数据 | 隐藏答案(内部) | 大小 |
|---|---|---|---|---|
| bmb_vendor_000001 | VCF→变异临床意义 | 18 变异匿名 VCF | PAH \| Phenylketonuria | 1.0KB |
| bmb_vendor_000002 | VCF→变异临床意义 | 18 变异匿名 VCF | ATP7B \| Wilson disease | 1.0KB |
| bmb_vendor_000003 | 序列→基因/病(BLAST) | 10 条匿名蛋白 FASTA | HEXA \| Tay-Sachs disease | 2.9KB |

买方格式 = `problems.csv`(列 id/question/answer_rubric/allowed_domains/human_solvable)+ `data/<ID>.zip`。

## 二、验收证据(独立验证,非自报)

**① 供应商门(`bmb_validator.py` · 买方 §3/§4/§5 译码)**:合并 3 题 → **0 REJECT / 0 WARN / exit 0**。

**② 真解验证(盲解:只读交付 zip,公共工具链独立解出)**:

| id | 盲解答案 | 唯一性 | 工具调用 | 难度(墙钟) |
|---|---|---|---|---|
| 000001 | PAH\|Phenylketonuria | 致病命中唯一=1 | 36(VEP 18+ClinVar 18) | 模型侧 20-30min |
| 000002 | ATP7B\|Wilson disease | 致病命中唯一=1 | 36 | 模型侧 20-30min |
| 000003 | HEXA\|Tay-Sachs disease | 溶酶体酶唯一=1 | 10 blastp | 1204s(供应商已知解法) |

- 难度守恒:VCF 题答案为 missense,藏在多个良性 missense 干扰里 → 不能靠"挑 impactful"蒙,必须逐个查库。
- 无泄露:盲解只读 zip 独立推出答案;建题期泄露断言(镜像验证器)+ 通用词(disease→condition/disorder)措辞规避。

## 三、数据真实性(买方跑 AI 检测的红线)

**全部真实数据,零 AI 凭空造**,每条可溯源:
- VCF 变异 = 真实 ClinVar 记录 + 真实 GRCh38 坐标(`canonical_spdi`),每条有 ClinVar VCV accession(见 `_INTERNAL_provenance.json`)。
- 蛋白序列 = 真实 NCBI RefSeq(Entrez efetch),每条有 NP_ accession。
- 匿名化 = 剥 rsID/INFO/基因名/致病性/FASTA 头 → 中性标签,答案不出现在任何交付文本/元数据。
- allowed_domains 全在买方 14 白名单内。

## 四、扩到 500 的生产环境(结论:不需要 GPU)

- 重计算全在 NCBI/Ensembl 服务器,本机只 Python;**任何阶段零 GPU**。
- 生产机 = 1 台普通 CPU 机 + 本地镜像库消限速:本地 ClinVar(已建 SQLite 420万/413MB,查询 **~13583× 提速**、结果一致)· 待补本地 VEP cache + SwissProt BLAST。
- 500 唯一性 QC:本地 ~1.5s(远程 16+h)。门槛在策展(~10-12 模板×数据集库)+ QC,不在算力。
- 详见 `../DESIGN_500_scale.md` + `../README.md`。

## 五、给买方的话(建议随交付)

- 这是 2 模板的试点批;两模板均过 bmb-infer 前置自检(格式/泄露/唯一/难度),请抽检。
- 全量 500 走"模板 × 真数据集库 × 自动化产-验管线",跨买方 8 类型铺开、反单调批次。
- 交付载体最终可上飞书多维表格 + 网页(本目录为文件形态源)。
