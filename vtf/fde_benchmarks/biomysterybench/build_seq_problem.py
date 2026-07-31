#!/usr/bin/env python3
"""BioMysteryBench 建题管线(蛋白序列→基因/疾病模板)· 第 2 模板。

对齐买方 qes1(FASTA→BLAST→身份)的 BLAST 范式,但用小数据(蛋白序列 KB 级)。
一道题 = 10 条真实人类蛋白序列(RefSeq,剥 FASTA 头 → seq_01..seq_10),
其中**恰好一条**是溶酶体酶(答案基因,其缺陷致某溶酶体贮积病),其余为胞质管家蛋白。
反向推理:BLAST 每条 → 识别基因 → 找出那条溶酶体酶 + 其疾病。

判别子 = **溶酶体定位**(客观可核查、唯一),不依赖"有没有病"这种模糊判断
(许多管家蛋白也有缺陷病,但都非溶酶体,故答案唯一)。

红线:真序列(RefSeq efetch),AI 不凭空造;答案基因/病名不进任何交付文本。

产出(--outdir,默认 ./_SEQ_out):
  problems.csv · data/<ID>.zip(sequences.fasta + README)· _source_manifest.json · answer_key.json
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import time
import zipfile
from pathlib import Path

from Bio import Entrez, SeqIO

Entrez.email = "fde-compass@nautilus.social"

PROBLEM_ID = "bmb_vendor_000003"

# 答案:溶酶体酶(其缺陷致溶酶体贮积病)· 病名清晰唯一
ANSWER_GENE = "HEXA"
ANSWER_CONDITION = "Tay-Sachs disease"
ANSWER_ALIASES = ["Tay-Sachs disease", "Tay Sachs", "GM2 gangliosidosis",
                  "hexosaminidase A deficiency", "hexosaminidase A (HEXA) deficiency"]

# 干扰:胞质管家/糖酵解/骨架蛋白(非溶酶体)· 身份 BLAST 明确
DISTRACTOR_GENES = ["GAPDH", "ENO1", "PKM", "LDHB", "ALDOA", "TPI1", "PGK1", "ACTB", "TUBA1B"]


def fetch_refseq_protein(gene: str, sleep=0.4):
    """取该基因的人类 RefSeq 蛋白序列(真实)。返回 (seq, accession, defline)。"""
    term = f"{gene}[Gene Name] AND Homo sapiens[Organism] AND refseq[Filter] AND NP_000000:NP_999999[Accession]"
    h = Entrez.esearch(db="protein", term=term, retmax=1)
    ids = Entrez.read(h)["IdList"]
    time.sleep(sleep)
    if not ids:  # 回退:放宽 NP_ 限制
        h = Entrez.esearch(db="protein", term=f"{gene}[Gene Name] AND Homo sapiens[Organism] AND refseq[Filter]", retmax=1)
        ids = Entrez.read(h)["IdList"]
        time.sleep(sleep)
    h = Entrez.efetch(db="protein", id=ids[0], rettype="fasta", retmode="text")
    rec = SeqIO.read(h, "fasta")
    time.sleep(sleep)
    return str(rec.seq), rec.id, rec.description


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, default=Path("_SEQ_out"))
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "data").mkdir(exist_ok=True)
    manifest_path = args.outdir / "_source_manifest.json"

    if manifest_path.exists() and not args.refresh:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"用缓存 manifest:{len(manifest['sequences'])} 条序列")
    else:
        print("从 NCBI 取真实 RefSeq 蛋白序列 ...")
        seqs = []
        answer_seq, answer_acc, answer_def = fetch_refseq_protein(ANSWER_GENE)
        seqs.append({"gene": ANSWER_GENE, "role": "answer", "accession": answer_acc,
                     "defline": answer_def, "seq": answer_seq, "localization": "lysosome"})
        print(f"  答案 {ANSWER_GENE}: {answer_acc} ({len(answer_seq)} aa)")
        for g in DISTRACTOR_GENES:
            try:
                s, acc, de = fetch_refseq_protein(g)
            except Exception as e:  # noqa: BLE001
                print(f"  ! {g} 取序列失败: {e!r}")
                continue
            seqs.append({"gene": g, "role": "distractor", "accession": acc,
                         "defline": de, "seq": s, "localization": "cytosol"})
            print(f"  干扰 {g}: {acc} ({len(s)} aa)")
        manifest = {"sequences": seqs,
                    "note": "全部为真实 RefSeq 人类蛋白序列(Entrez efetch protein)"}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    seqs = manifest["sequences"]

    # 唯一性硬校验:恰好一条溶酶体酶(答案)
    lyso = [s for s in seqs if s.get("localization") == "lysosome"]
    assert len(lyso) == 1 and lyso[0]["gene"] == ANSWER_GENE, "溶酶体酶不唯一"

    # 匿名化:剥 FASTA 头 → seq_NN,确定性打乱顺序
    rng = random.Random(20260716)
    order = list(range(len(seqs)))
    rng.shuffle(order)
    fasta_lines = []
    labelmap = {}
    for new_idx, orig_idx in enumerate(order, 1):
        s = seqs[orig_idx]
        label = f"seq_{new_idx:02d}"
        labelmap[label] = s["gene"]
        seq = s["seq"]
        fasta_lines.append(f">{label}")
        for i in range(0, len(seq), 60):
            fasta_lines.append(seq[i:i + 60])
    fasta_text = "\n".join(fasta_lines) + "\n"

    # 泄露自检:答案基因/病名/accession 绝不能出现在 FASTA
    low = fasta_text.lower()
    for leak in (ANSWER_GENE.lower(), *[a.lower() for a in ANSWER_ALIASES],
                 lyso[0]["accession"].lower(), "hexosaminidase"):
        assert leak not in low, f"FASTA 泄露答案 token: {leak}"

    zip_path = args.outdir / "data" / f"{PROBLEM_ID}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("sequences.fasta", fasta_text)  # 纯数据 zip(对齐买方 qes1;任务全在 question)

    # 自然简洁题干(对齐买方 qes1 风格:一句直问,无背景铺垫/无工具说明/无格式模板)
    question = (
        "One of these protein sequences is a lysosomal enzyme — which gene encodes it, "
        "and what disorder does its deficiency cause?"
    )

    rubric = (
        f"The answer is {ANSWER_GENE} / {ANSWER_CONDITION}. "
        f"Accept the gene {ANSWER_GENE} and the disorder named as any of: {', '.join(ANSWER_ALIASES)}. "
        "Score 1.0 only if the response gives both the correct gene and the correct disorder; "
        "score 0.0 otherwise (all-or-nothing, no partial credit)."
    )
    allowed_domains = (
        "conda.anaconda.org, repo.anaconda.com, ncbi.nlm.nih.gov, ftp.ncbi.nlm.nih.gov, "
        "ensembl.org, ftp.ensembl.org, hgdownload.soe.ucsc.edu, uniprot.org, bioconductor.org, "
        "pypi.org, bioconda.github.io, cran.r-project.org, cran.rstudio.com, ftp.ebi.ac.uk"
    )

    # 建题期泄露断言(镜像 bmb_validator)
    from bmb_validator import _answer_tokens
    for tok in _answer_tokens(f"{ANSWER_GENE}|{ANSWER_CONDITION}"):
        assert not re.search(r"\b" + re.escape(tok) + r"\b", question.lower()), \
            f"答案 token '{tok}' 泄露在 question"
        assert not re.search(r"\b" + re.escape(tok) + r"\b", PROBLEM_ID.lower()), \
            f"答案 token '{tok}' 泄露在 id"

    with open(args.outdir / "problems.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "question", "answer_rubric", "allowed_domains", "human_solvable"])
        w.writerow([PROBLEM_ID, question, rubric, allowed_domains, "yes"])

    (args.outdir / "answer_key.json").write_text(
        json.dumps({"id": PROBLEM_ID, "gene": ANSWER_GENE, "condition": ANSWER_CONDITION,
                    "answer_label": [k for k, v in labelmap.items() if v == ANSWER_GENE][0],
                    "labelmap": labelmap, "n_sequences": len(seqs)},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ 建题完成:{len(seqs)} 序列(1 溶酶体酶 {ANSWER_GENE}/{ANSWER_CONDITION} + {len(seqs)-1} 干扰)")
    print(f"   {args.outdir / 'problems.csv'}")
    print(f"   {zip_path}  ({zip_path.stat().st_size} B)")
    print(f"   泄露自检通过(FASTA 不含答案 token)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
