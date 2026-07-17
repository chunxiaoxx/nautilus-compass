# BioMysteryBench 出题脚手架(compass · FDE benchmark turf)

> 甲方外部需求《BioMysteryBench 数据要求【外部】》(2026-07-16 收)。
> 本目录 = **格式规范 + 供应商侧验证器**。起步阶段(用户拍:先做脚手架 · 本机 · 优先级先评估)。
> 🔴 红线:题目内容需真专家/真数据,**AI 不得凭空造**;交付前必须**真把题解出来**验证唯一答案+难度,否则买方 bmb-infer 退回。

## 一道合格题 = 什么

| 组成 | 说明 |
|---|---|
| `problems.csv` 一行 | 列 = `id, question, answer_rubric, allowed_domains, human_solvable` |
| `data/<ID>.zip` | 该题工作空间(真实生物数据:FASTA/BAM/mzML/计数表/变异…),作答前解压到干净目录 |

**核心风格**:信息**反向推理**——从证据反推隐藏事实(身份/来源/变体/功能/实验条件)。
样例(买方给的 qes1):给 721MB `SRR1295350.fasta` → 问"这是什么癌?" → 答 `Glioblastoma/GBM`。

## 验收门(买方 §3/§4/§5 · 已译成 `bmb_validator.py`)

**REJECT(会被买方退回,必须修)**
- 缺必填列 / id 与 `data/<ID>.zip` 不匹配 / zip 缺失/损坏/空
- `allowed_domains` 超出 14 域名白名单
- `human_solvable != yes`
- **答案泄露**:标准答案词出现在 question / id / 文件名 / 元数据(§3 红线)

**WARN(人工复核 · 自动判不准的项)**
- rubric 未明确全对全错(1.0/0)
- 难度疑过低(计数/求和/平均类)、疑无需工具、未说明答案格式
- rubric 抽不到标准答案(泄露检查跳过)

**自动判不了、必须人肉/真解的(买方 §4/§5 核心)**
- **20-30 分钟难度 + ≥10 次工具调用**:只能靠真解一遍计时。
- **唯一答案**:必须真跑工具链确认答案唯一、无歧义。
- 这就是为什么**交付前要搭 bio 工具环境把每题解出来**——验证器只挡格式/泄露/白名单,挡不住"题太水"或"答案不唯一"。

## 用法

```bash
# 内置样例自检(qes1 GBM + 泄露负例)
python bmb_validator.py --selftest

# 验一批交付
python bmb_validator.py problems.csv --data-dir ./data
# 退出码 0 = 无 REJECT;非 0 = 有 REJECT
```

## 白名单域名(14 · 买方 §3)
conda.anaconda.org · repo.anaconda.com · ncbi.nlm.nih.gov · ftp.ncbi.nlm.nih.gov ·
ensembl.org · ftp.ensembl.org · hgdownload.soe.ucsc.edu · uniprot.org ·
bioconductor.org · pypi.org · bioconda.github.io · cran.r-project.org ·
cran.rstudio.com · ftp.ebi.ac.uk

## P1 管线(VCF→变异临床意义 · 2026-07-16 端到端跑通)

一道题 = 1 个隐藏 ClinVar **Pathogenic** 变异(答案)+ N 个 Benign/VUS 干扰变异,
全部真实 ClinVar 记录 + 真实 GRCh38 坐标(`canonical_spdi`),组装成匿名 VCF
(剥 rsID/INFO/基因名/致病性)→ 反向推理"哪个基因 + 什么病"。

```bash
python build_problem.py    # 建题:拉真干扰项(缓存溯源)+ 组装匿名 VCF → _P1_out/
python bmb_validator.py _P1_out/problems.csv --data-dir _P1_out/data   # 格式/泄露门
python solve_problem.py _P1_out/data/bmb_vendor_000001.zip             # 盲解:只读 zip,VEP+ClinVar 独立解 + 验唯一性
```

- `build_problem.py` — 建题管线。`_source_manifest.json` = 每变异 ClinVar accession 溯源(审计);`answer_key.json` = 本地答案(不进 zip)。
- `solve_problem.py` — 盲解 QC:模拟买方 bmb-infer,只读交付 zip,坐实答案可推+唯一+工具数。

**P1 实测(bmb_vendor_000001 · PAH/Phenylketonuria · 独立验证非自报)**:
- ① 1 行 problems.csv + data/*.zip(18 变异,答案埋中间,全剥注释)
- ② bmb_validator **0 REJECT / 0 WARN / exit 0**
- ③ 盲解 → `PAH|Phenylketonuria`,致病命中**唯一 =1**,工具调用 **36 次**(VEP 18 + ClinVar 18,门 ≥10),无泄露
- **难度守恒**:答案是 missense,9 个干扰项也是 missense → 不能"挑 impactful 的"蒙,必须逐个查 ClinVar → 模型侧真 20-30min/多工具(我们知解法所以 131s,模型不知所以慢)

## 解题工具链(供应商已验通)
- **Ensembl VEP REST**(`rest.ensembl.org/vep/human/region/...`):坐标 → 基因 + 最重后果。
- **NCBI ClinVar E-utilities**(`{chr}[chr] AND {pos}[chrpos38]`):GRCh38 坐标 → 临床分类 + 疾病。
- 本机 Windows Python 3.13 + Biopython 1.87,两通道实连(WSL 网坏不用;小数据无需本地重工具)。

## 进展(2026-07-17 · 3 题 / 2 模板 / 批产地基 / 本地镜像)

**模板 1 · VCF→变异临床意义**(`build_problem.py` 已参数化 `--answer-gene`,自动挑 Pathogenic missense + 排除同基因干扰 → 可批产):
- #1 `bmb_vendor_000001` PAH/Phenylketonuria · #2 `bmb_vendor_000002` ATP7B/Wilson disease
- 各 18 变异,0 REJECT,盲解致病唯一=1,36 工具调用。

**模板 2 · 序列→基因/病(BLAST)**(`build_seq_problem.py` / `solve_seq_problem.py`,对齐买方 qes1 的 BLAST 范式,小数据):
- #3 `bmb_vendor_000003` HEXA/Tay-Sachs:10 条真 RefSeq 蛋白剥头,恰好 1 条溶酶体酶(判别子=定位,可核查唯一)。
- 0 REJECT,盲解 10 blastp 全干净,溶酶体酶唯一=1,**墙钟 1204s(压中 20-30min 难度档)**。远程 BLAST 会瞬时 SSL 抖动 → solve 已加退避重试。

**本地镜像(Windows 原生 · 零 GPU/WSL · 消 Entrez 限速)**:
```bash
python build_local_clinvar.py _localdb/clinvar_grch38.vcf.gz  # clinvar.vcf.gz→SQLite(420万/413MB/67s)
python qc_vcf_local.py _P1_out/data/bmb_vendor_000001.zip     # 本地批量 QC(唯一性)· 毫秒级
```
- 实测:本地 **0.20ms/查** vs 远程 **2715ms/查** = **~13583× 提速**,结果 **5/5 一致**。
- #1/#2 本地 QC 各 3ms,致病唯一=1 → 500 题唯一性 QC ≈ 1.5s(远程要 16+h)。

## 500 题生产环境(结论:不需要 GPU)
- **重计算都在 NCBI/Ensembl 服务器**(API/远程 BLAST),本机只 Python;任何阶段零 GPU。
- 生产机 = 1 台普通 CPU Linux/Windows + 本地镜像库(消限速):
  - ✅ 本地 ClinVar(clinvar.vcf.gz→SQLite,已建)· ⏳ 本地 VEP offline cache(~25GB,GRCh38)· ⏳ 本地 BLAST+ SwissProt(~90MB,序列题那半)。
  - `nr` 大库(~200GB)仅个别模板需;死守小数据模板(KB-MB),避 qes1 那种 721MB FASTA(500× = TB 级)。
- WSL 网坏根因 = `.wslconfig` mirrored 模式 + docker-desktop 冲突;**用不着 WSL**(BLAST+ 有 win64、ClinVar Python 解析、snpEff Java)。真要 Linux 环境走 NAT 一条配置改,别重建。
- 门槛在**策展(~10-12 模板×数据集库)+ QC 时间**,不在算力;本地镜像后 QC 从小时级降到秒级。

## 下一步(需拍优先级)
1. 镜像本地 SwissProt BLAST + VEP cache → 序列/VCF 题 QC 全本地秒级。
2. P2 扩模板库(表达谱→癌型、峰→TF…)覆盖买方 8 类型 + 反单调。
3. P3 编排(断点+跨模板配额)→ P4 批产 + 抽样真解 QC。
- ⚠️ 验证器 WARN 启发式偏严:买方 qes1 也触发 2 WARN。WARN 只复核不拦交付。
