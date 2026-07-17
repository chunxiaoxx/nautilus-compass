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

## 状态 / 下一步(诚实)

- ✅ **已做**:格式规范 + 验证器(自检过 + 买方真实样例 qes1 实测过)。
- ⏳ **待做(需你拍优先级)**:
  1. 搭本机 bio 工具环境(WSL/conda + bioconda:BLAST/samtools/bcftools…)——**真解题验证的前提**。
  2. 端到端产+解+验 1 道题(复现 qes1 或基于公开 SRA 造新题),证明管线过买方验收档。
  3. 跑通后再定批量 + 是否设为主线(vs 现有 11 题 / GenOpt 新题供给)。
- ⚠️ 验证器的 WARN 启发式偏严:买方自己的 qes1 也触发 2 个 WARN(题干简短没点明工具/格式)。WARN 只是复核提示、不拦交付;后续可按真实批次校准。
