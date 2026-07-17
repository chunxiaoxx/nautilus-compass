#!/usr/bin/env python3
"""BioMysteryBench 建题管线(VCF→变异临床意义模板)· P1 雏形。

一道题 = 1 个隐藏的 ClinVar Pathogenic 变异(答案)+ N 个 Benign/VUS 干扰变异,
全部为**真实 ClinVar 记录 + 真实 GRCh38 坐标**(canonical_spdi 权威表示),
组装成匿名 VCF(剥 rsID/INFO/基因名/致病性),问"哪个基因 + 什么病"。

红线:真数据真坐标,AI 不凭空造。每个变异都可溯源到 ClinVar accession(见 _source_manifest.json)。
唯一重人工环节 = 策展(选 1 致病 + 若干良性),这正是买方要的"元数据挖掘/生信判断"。

产出(--outdir,默认 ./_P1_out):
  problems.csv          买方格式一行
  data/<ID>.zip         匿名 VCF 工作空间(交付给解题模型)
  _source_manifest.json 每个变异的 ClinVar 溯源(供应商审计,不交付)
  answer_key.json       答案(仅供本地 solve 验证,绝不进 zip / 不交付)

用法:
  python build_problem.py                 # 用缓存 manifest(若无则联网拉)
  python build_problem.py --refresh        # 强制重新从 ClinVar 拉干扰项
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import time
import zipfile
from pathlib import Path

from Bio import Entrez

Entrez.email = "fde-compass@nautilus.social"

PROBLEM_ID = "bmb_vendor_000001"

# 答案变异(已独立验证:VEP→PAH/missense · ClinVar 坐标查→Pathogenic/Phenylketonuria)
ANSWER = {
    "chrom": "12", "pos": 102846899, "ref": "G", "alt": "T",
    "spdi": "NC_000012.12:102846898:G:T",
    "gene": "PAH", "condition": "Phenylketonuria",
    "clinvar_cls": "Pathogenic",
}

# 干扰项来源基因(真实 panel 常见基因)· 取其 Benign/Likely benign/VUS SNV
DISTRACTOR_GENES = [
    ("BRCA2", "benign"), ("BRCA1", "benign"), ("CFTR", "benign"),
    ("MYH7", "benign"), ("SCN5A", "benign"), ("LDLR", "benign"),
    ("MSH2", "benign"), ("MLH1", "benign"), ("APOB", "benign"),
    ("TTN", "benign"), ("PALB2", "benign"), ("RYR1", "benign"),
    ("COL1A1", "benign"), ("FBN1", "benign"), ("GJB2", "benign"),
    ("TP53", "benign"), ("APC", "benign"), ("PKD1", "benign"),
]

# 绝不能进干扰池的分类(保证答案唯一)
PATHOGENIC_CLS = {"Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"}

CONTIG_LEN = {  # GRCh38 染色体长度(用于 ##contig 头)
    "1": 248956422, "2": 242193529, "3": 198295559, "6": 170805979,
    "7": 159345973, "11": 135086622, "12": 133275309, "13": 114364328,
    "14": 107043718, "15": 101991189, "16": 90338345, "17": 83257441,
    "19": 58617616, "2L": 0,
}


def _spdi_to_vcf(spdi: str):
    seq, p0, ref, alt = spdi.split(":")
    return int(p0) + 1, ref, alt  # SPDI 0-based → VCF 1-based


def fetch_distractors(genes, need, sleep=0.45):
    """从 ClinVar 拉真实 Benign/VUS SNV 干扰项。每个都记录溯源 + 确认非致病。"""
    out = []
    for gene, sig in genes:
        if len(out) >= need:
            break
        try:
            h = Entrez.esearch(db="clinvar", term=f"{gene}[gene] AND {sig}[clinsig]", retmax=25)
            ids = Entrez.read(h)["IdList"]
            time.sleep(sleep)
            if not ids:
                continue
            h = Entrez.esummary(db="clinvar", id=",".join(ids[:25]), retmode="json")
            d = json.load(h)["result"]
            time.sleep(sleep)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {gene} fetch 失败: {e!r}")
            continue
        for uid in d.get("uids", []):
            res = d[uid]
            vs = (res.get("variation_set") or [{}])[0]
            spdi = vs.get("canonical_spdi", "")
            if spdi.count(":") != 3:
                continue
            seq, p0, ref, alt = spdi.split(":")
            if not (seq.startswith("NC_0000") and len(ref) == 1 == len(alt) and ref and alt):
                continue
            gc = res.get("germline_classification", {})
            cls = gc.get("description", "")
            if cls in PATHOGENIC_CLS:  # 保证唯一:跳过任何致病干扰项
                continue
            chrom = _seq_to_chrom(seq)
            if chrom not in CONTIG_LEN:
                continue
            pos, r, a = _spdi_to_vcf(spdi)
            out.append({
                "chrom": chrom, "pos": pos, "ref": r, "alt": a, "spdi": spdi,
                "gene": gene, "clinvar_cls": cls, "accession": res.get("accession"),
                "title": res.get("title"),
            })
            break  # 每基因取一个,保证多样性
    return out[:need]


def _seq_to_chrom(refseq: str) -> str:
    """NC_000012.12 → '12';NC_000023 → 'X';NC_000024 → 'Y'。"""
    try:
        n = int(refseq.split(".")[0].replace("NC_0000", ""))
    except ValueError:
        return refseq
    return {23: "X", 24: "Y"}.get(n, str(n))


def build_vcf(variants, sample="SAMPLE_01") -> str:
    """组装匿名 VCF:剥 rsID(ID='.')/INFO('.')/基因名/致病性,只留坐标 + GT。"""
    chroms = sorted({v["chrom"] for v in variants}, key=lambda c: (len(c), c))
    lines = [
        "##fileformat=VCFv4.2",
        "##reference=GRCh38",
        "##source=targeted_sequencing_panel",
        '##FILTER=<ID=PASS,Description="All filters passed">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
    ]
    for c in chroms:
        lines.append(f"##contig=<ID={c},length={CONTIG_LEN.get(c, 0)},assembly=GRCh38>")
    lines.append("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + sample)
    # 按基因组坐标排序(真实 VCF 惯例)——不泄露答案位置
    for v in sorted(variants, key=lambda x: (int(x["chrom"]) if x["chrom"].isdigit() else 99, x["pos"])):
        gt = v.get("gt", "0/1")
        lines.append(f"{v['chrom']}\t{v['pos']}\t.\t{v['ref']}\t{v['alt']}\t.\tPASS\t.\tGT\t{gt}")
    return "\n".join(lines) + "\n"


SOLVER_README = """\
# 变异解读挑战 · 工作空间

`variants.vcf` 是某个体一次靶向测序 panel 的变异结果(参考基因组见 VCF 头)。
其中**恰好一个**变异是已确立的致病变异,导致一种单基因遗传病;其余为良性或意义未明。

任务:识别该致病变异所在的**基因**及其**关联疾病**。
提交格式:`GENE|Disease`(例:`XXXX|Some disease`)。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, default=Path("_P1_out"))
    ap.add_argument("--refresh", action="store_true", help="强制重拉干扰项(否则用缓存 manifest)")
    ap.add_argument("--n-distractors", type=int, default=17)
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "data").mkdir(exist_ok=True)
    manifest_path = args.outdir / "_source_manifest.json"

    if manifest_path.exists() and not args.refresh:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        distractors = manifest["distractors"]
        print(f"用缓存 manifest:{len(distractors)} 个干扰项")
    else:
        print(f"从 ClinVar 拉 {args.n_distractors} 个真实干扰项 ...")
        distractors = fetch_distractors(DISTRACTOR_GENES, args.n_distractors)
        manifest = {"answer": ANSWER, "distractors": distractors,
                    "note": "全部变异均为真实 ClinVar 记录 + 真实 GRCh38 坐标(canonical_spdi)"}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  拉到 {len(distractors)} 个;溯源写入 {manifest_path.name}")

    # 唯一性硬校验:干扰池内不得有致病变异
    bad = [d for d in distractors if d["clinvar_cls"] in PATHOGENIC_CLS]
    if bad:
        print(f"🔴 干扰池含致病变异,答案不唯一:{[b['gene'] for b in bad]}")
        return 1

    # 组装变异集(答案 het,干扰项确定性混合基因型)
    rng = random.Random(20260716)
    answer_v = dict(ANSWER, gt="0/1")
    dvars = []
    for d in distractors:
        dvars.append(dict(d, gt=rng.choice(["0/1", "1/1", "0/1"])))
    all_variants = [answer_v] + dvars

    vcf_text = build_vcf(all_variants)

    # 泄露自检:答案基因/病名绝不能出现在 VCF 文本
    low = vcf_text.lower()
    for leak in (ANSWER["gene"].lower(), ANSWER["condition"].lower()):
        assert leak not in low, f"VCF 泄露答案 token: {leak}"

    # 打包 data/<ID>.zip
    zip_path = args.outdir / "data" / f"{PROBLEM_ID}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("variants.vcf", vcf_text)
        z.writestr("README.md", SOLVER_README)

    # problems.csv 一行
    question = (
        "The file data/{id}.zip contains variants.vcf — variant calls from one individual's "
        "targeted sequencing panel (reference genome stated in the VCF header). Exactly one "
        "variant is a well-established pathogenic variant that causes a single-gene Mendelian "
        "disorder; all others are benign or of uncertain significance. Using variant-annotation "
        "tooling and public variant databases (Ensembl VEP, NCBI ClinVar/dbSNP over the allowed "
        "domains), determine which gene carries that pathogenic variant and the associated "
        "disease. Answer strictly in the format GENE|Disease (HGNC gene symbol, then the disease "
        "name), e.g. XXXX|Some disease."
    ).format(id=PROBLEM_ID)

    rubric = (
        "Scoring is all-or-nothing (1.0 or 0.0, no partial credit). "
        "The answer is PAH|Phenylketonuria. "
        "Score 1.0 only if the response identifies BOTH the gene PAH AND the disease "
        "(any of: Phenylketonuria, PKU, phenylalanine hydroxylase deficiency, hyperphenylalaninemia); "
        "the causal variant is the missense change at GRCh38 chr12:102846899 G>T "
        "(NM_000277.3(PAH):c.965C>A, p.Ala322Asp, ClinVar Pathogenic). Score 0.0 otherwise, including if the "
        "model reports any other gene or reaches the answer by inspecting file metadata rather than "
        "annotating the variants."
    )
    allowed_domains = "ncbi.nlm.nih.gov, ensembl.org, pypi.org, bioconda.github.io"

    csv_path = args.outdir / "problems.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "question", "answer_rubric", "allowed_domains", "human_solvable"])
        w.writerow([PROBLEM_ID, question, rubric, allowed_domains, "yes"])

    # answer_key.json(仅本地验证,不进 zip)
    (args.outdir / "answer_key.json").write_text(
        json.dumps({"id": PROBLEM_ID, "gene": ANSWER["gene"], "condition": ANSWER["condition"],
                    "spdi": ANSWER["spdi"], "n_variants": len(all_variants)},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ 建题完成:{len(all_variants)} 变异(1 致病 + {len(dvars)} 干扰)")
    print(f"   {csv_path}")
    print(f"   {zip_path}  ({zip_path.stat().st_size} B)")
    print(f"   泄露自检通过(VCF 不含 '{ANSWER['gene']}' / '{ANSWER['condition']}')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
