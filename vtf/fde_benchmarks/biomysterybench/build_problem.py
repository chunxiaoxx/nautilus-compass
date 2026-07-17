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
import urllib.request
import zipfile
from pathlib import Path

from Bio import Entrez

Entrez.email = "fde-compass@nautilus.social"

# 默认答案变异(已独立验证:VEP→PAH/missense · ClinVar 坐标查→Pathogenic/Phenylketonuria)
DEFAULT_ANSWER = {
    "chrom": "12", "pos": 102846899, "ref": "G", "alt": "T",
    "spdi": "NC_000012.12:102846898:G:T",
    "gene": "PAH", "condition": "Phenylketonuria",
    "clinvar_cls": "Pathogenic",
    "hgvs": "NM_000277.3(PAH):c.965C>A, p.Ala322Asp",
}

# 疾病别名(all-or-nothing rubric 接受的等价答案)· 无条目则只用 ClinVar 病名
CONDITION_ALIASES = {
    "Phenylketonuria": ["Phenylketonuria", "PKU", "phenylalanine hydroxylase deficiency",
                        "hyperphenylalaninemia"],
    "Wilson disease": ["Wilson disease", "Wilson's disease", "hepatolenticular degeneration"],
    "Tay-Sachs disease": ["Tay-Sachs disease", "Tay Sachs", "GM2 gangliosidosis",
                          "hexosaminidase A deficiency"],
    "Galactosemia": ["Galactosemia", "classic galactosemia", "GALT deficiency"],
    "Alpha-1-antitrypsin deficiency": ["Alpha-1-antitrypsin deficiency", "AATD", "A1AT deficiency"],
}

# 买方 §3 全 14 白名单(qes1 即列全 14,给模型足够自由度,避免卡在没列的资源)
ALLOWED_DOMAINS_14 = (
    "conda.anaconda.org, repo.anaconda.com, ncbi.nlm.nih.gov, ftp.ncbi.nlm.nih.gov, "
    "ensembl.org, ftp.ensembl.org, hgdownload.soe.ucsc.edu, uniprot.org, bioconductor.org, "
    "pypi.org, bioconda.github.io, cran.r-project.org, cran.rstudio.com, ftp.ebi.ac.uk"
)

# 干扰项来源基因(真实 panel 常见基因)· 取其 Benign/Likely benign/VUS SNV · 数量上调消 F2 难度风险
DISTRACTOR_GENES = [
    ("BRCA2", "benign"), ("BRCA1", "benign"), ("CFTR", "benign"),
    ("MYH7", "benign"), ("SCN5A", "benign"), ("LDLR", "benign"),
    ("MSH2", "benign"), ("MLH1", "benign"), ("APOB", "benign"),
    ("TTN", "benign"), ("PALB2", "benign"), ("RYR1", "benign"),
    ("COL1A1", "benign"), ("FBN1", "benign"), ("GJB2", "benign"),
    ("TP53", "benign"), ("APC", "benign"), ("PKD1", "benign"),
    ("KCNQ1", "benign"), ("KCNH2", "benign"), ("PKP2", "benign"),
    ("DSP", "benign"), ("LMNA", "benign"), ("ATM", "benign"),
    ("CHEK2", "benign"), ("PMS2", "benign"), ("PTEN", "benign"),
    ("TSC2", "benign"), ("VHL", "benign"), ("RET", "benign"),
    ("NF1", "benign"), ("SMAD4", "benign"), ("STK11", "benign"),
    ("RAD51C", "benign"), ("NBN", "benign"), ("DSG2", "benign"),
]

# 绝不能进干扰池的分类(保证答案唯一)
PATHOGENIC_CLS = {"Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"}

CONTIG_LEN = {  # GRCh38 染色体长度(用于 ##contig 头)
    "1": 248956422, "2": 242193529, "3": 198295559, "4": 190214555,
    "5": 181538259, "6": 170805979, "7": 159345973, "8": 145138636,
    "9": 138394717, "10": 133797422, "11": 135086622, "12": 133275309,
    "13": 114364328, "14": 107043718, "15": 101991189, "16": 90338345,
    "17": 83257441, "18": 80373285, "19": 58617616, "20": 64444167,
    "21": 46709983, "22": 50818468, "X": 156040895, "Y": 57227415,
}


def _spdi_to_vcf(spdi: str):
    seq, p0, ref, alt = spdi.split(":")
    return int(p0) + 1, ref, alt  # SPDI 0-based → VCF 1-based


def _vep_consequence(chrom, pos, alt, sleep=0.2):
    """Ensembl VEP:坐标 → (基因集, 最重后果)。用于建题时确认答案变异是 missense。"""
    url = (f"https://rest.ensembl.org/vep/human/region/"
           f"{chrom}:{pos}-{pos}:1/{alt}?content-type=application/json")
    req = urllib.request.Request(url, headers={"User-Agent": "compass-bmb-build"})
    v = json.load(urllib.request.urlopen(req, timeout=30))[0]
    time.sleep(sleep)
    genes = sorted({t.get("gene_symbol") for t in v.get("transcript_consequences", [])
                    if t.get("gene_symbol")})
    return genes, v.get("most_severe_consequence")


def resolve_answer(gene: str, sleep=0.45) -> dict:
    """为答案基因挑一个 Pathogenic **missense** SNV(单一清晰病名)。
    missense = 难度守恒(藏在良性 missense 干扰里,模型不能靠后果类型蒙)。"""
    h = Entrez.esearch(db="clinvar", term=f"{gene}[gene] AND pathogenic[clinsig]", retmax=40)
    ids = Entrez.read(h)["IdList"]
    time.sleep(sleep)
    if not ids:
        raise SystemExit(f"🔴 {gene} 无 Pathogenic 记录")
    for chunk in [ids[i:i + 20] for i in range(0, len(ids), 20)]:
        h = Entrez.esummary(db="clinvar", id=",".join(chunk), retmode="json")
        d = json.load(h)["result"]
        time.sleep(sleep)
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
            if gc.get("description") != "Pathogenic":
                continue
            conds = [t.get("trait_name") for t in gc.get("trait_set", [])
                     if t.get("trait_name") not in (None, "not specified", "not provided")]
            if len(conds) != 1:
                continue
            chrom = _seq_to_chrom(seq)
            pos, r, a = _spdi_to_vcf(spdi)
            genes, cons = _vep_consequence(chrom, pos, a)
            if cons != "missense_variant" or gene not in genes:
                continue
            return {"chrom": chrom, "pos": pos, "ref": r, "alt": a, "spdi": spdi,
                    "gene": gene, "condition": conds[0], "clinvar_cls": "Pathogenic",
                    "hgvs": res.get("title", "")}
    raise SystemExit(f"🔴 {gene} 未找到合适的 Pathogenic missense SNV(换基因)")


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, default=Path("_P1_out"))
    ap.add_argument("--refresh", action="store_true", help="强制重拉干扰项(否则用缓存 manifest)")
    ap.add_argument("--n-distractors", type=int, default=29)
    ap.add_argument("--id", default="bmb_vendor_000001", help="题 id(= data/<ID>.zip)")
    ap.add_argument("--answer-gene", default=None,
                    help="答案基因(自动挑 Pathogenic missense);缺省用已验证的 PAH")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "data").mkdir(exist_ok=True)
    manifest_path = args.outdir / "_source_manifest.json"

    # 解析答案变异
    if args.answer_gene:
        print(f"解析答案基因 {args.answer_gene}(挑 Pathogenic missense)...")
        answer = resolve_answer(args.answer_gene)
        print(f"  → {answer['gene']} {answer['condition']} @ chr{answer['chrom']}:{answer['pos']} "
              f"({answer['hgvs']})")
    else:
        answer = dict(DEFAULT_ANSWER)

    if manifest_path.exists() and not args.refresh:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        distractors = manifest["distractors"]
        print(f"用缓存 manifest:{len(distractors)} 个干扰项")
    else:
        print(f"从 ClinVar 拉 {args.n_distractors} 个真实干扰项 ...")
        # 干扰项排除与答案同基因(避免同基因致病/良性混淆)
        genes = [(g, s) for g, s in DISTRACTOR_GENES if g != answer["gene"]]
        distractors = fetch_distractors(genes, args.n_distractors)
        manifest = {"answer": answer, "distractors": distractors,
                    "note": "全部变异均为真实 ClinVar 记录 + 真实 GRCh38 坐标(canonical_spdi)"}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  拉到 {len(distractors)} 个;溯源写入 {manifest_path.name}")

    # 唯一性硬校验:干扰池内不得有致病变异 / 不得与答案同基因
    bad = [d for d in distractors if d["clinvar_cls"] in PATHOGENIC_CLS or d["gene"] == answer["gene"]]
    if bad:
        print(f"🔴 干扰池含致病变异或与答案同基因,答案不唯一:{[b['gene'] for b in bad]}")
        return 1

    # 组装变异集(答案 het,干扰项确定性混合基因型)
    rng = random.Random(20260716)
    answer_v = dict(answer, gt="0/1")
    dvars = [dict(d, gt=rng.choice(["0/1", "1/1", "0/1"])) for d in distractors]
    all_variants = [answer_v] + dvars

    vcf_text = build_vcf(all_variants)

    # 泄露自检:答案基因/病名绝不能出现在 VCF 文本
    low = vcf_text.lower()
    for leak in (answer["gene"].lower(), answer["condition"].lower()):
        assert leak not in low, f"VCF 泄露答案 token: {leak}"

    # 打包 data/<ID>.zip
    zip_path = args.outdir / "data" / f"{args.id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("variants.vcf", vcf_text)  # 纯数据 zip(对齐买方 qes1;任务全在 question)

    # problems.csv 一行
    question = (
        "The file data/{id}.zip contains variants.vcf — variant calls from one individual's "
        "targeted sequencing panel (reference genome stated in the VCF header). Exactly one "
        "variant is a well-established pathogenic variant that causes a single-gene Mendelian "
        "condition; all others are benign or of uncertain significance. Investigate the variants "
        "using variant-annotation and database-lookup workflows over the public resources listed in "
        "allowed_domains, and determine which gene carries that pathogenic variant and the condition "
        "it causes. Answer strictly in the format GENE|Condition (HGNC gene symbol, then the "
        "condition name), e.g. XXXX|Some condition."
    ).format(id=args.id)

    aliases = CONDITION_ALIASES.get(answer["condition"], [answer["condition"]])
    rubric = (
        "Scoring is all-or-nothing (1.0 or 0.0, no partial credit). "
        f"The answer is {answer['gene']}|{answer['condition']}. "
        f"Score 1.0 only if the response identifies BOTH the gene {answer['gene']} AND the disease "
        f"(any of: {', '.join(aliases)}); the causal variant is the missense change at GRCh38 "
        f"chr{answer['chrom']}:{answer['pos']} {answer['ref']}>{answer['alt']} "
        f"({answer['hgvs']}, ClinVar Pathogenic). Score 0.0 otherwise, including if the "
        "model reports any other gene or reaches the answer by inspecting file metadata rather than "
        "annotating the variants."
    )
    allowed_domains = ALLOWED_DOMAINS_14

    # 建题期泄露断言(镜像 bmb_validator:答案 token 不得出现在 question/id)
    import re as _re
    from bmb_validator import _answer_tokens
    for tok in _answer_tokens(f"{answer['gene']}|{answer['condition']}"):
        assert not _re.search(r"\b" + _re.escape(tok) + r"\b", question.lower()), \
            f"答案 token '{tok}' 泄露在 question(先修措辞)"
        assert not _re.search(r"\b" + _re.escape(tok) + r"\b", args.id.lower()), \
            f"答案 token '{tok}' 泄露在 id"

    csv_path = args.outdir / "problems.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "question", "answer_rubric", "allowed_domains", "human_solvable"])
        w.writerow([args.id, question, rubric, allowed_domains, "yes"])

    # answer_key.json(仅本地验证,不进 zip)
    (args.outdir / "answer_key.json").write_text(
        json.dumps({"id": args.id, "gene": answer["gene"], "condition": answer["condition"],
                    "spdi": answer["spdi"], "n_variants": len(all_variants)},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ 建题完成:{len(all_variants)} 变异(1 致病 {answer['gene']}/{answer['condition']} + {len(dvars)} 干扰)")
    print(f"   {csv_path}")
    print(f"   {zip_path}  ({zip_path.stat().st_size} B)")
    print(f"   泄露自检通过(VCF 不含 '{answer['gene']}' / '{answer['condition']}')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
