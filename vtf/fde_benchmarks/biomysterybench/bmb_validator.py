#!/usr/bin/env python3
"""BioMysteryBench 供应商侧验证器 · 交付前自检买方验收门。

把买方《BioMysteryBench 数据要求【外部】》§3/§4/§5 的验收标准译成可执行检查,
在交付前跑一遍,拦掉会被买方 bmb-infer 退回的题(泄露/无工具/格式/难度过低)。

用法:
    python bmb_validator.py problems.csv --data-dir ./data
    python bmb_validator.py --selftest        # 用内置 qes1(GBM)样例自检

判据来源(买方 PDF):
  §3 格式    · 列 = id,question,answer_rubric,allowed_domains,human_solvable
             · id 必须与 data/<ID>.zip 文件名匹配
             · 提示词/列名/文件名/元数据中不得透露答案
  §4 质量    · 全对全错评分(1.0/0,无部分分)· 唯一答案 · 需外部工具 · 20-30min 难度
  §5 验收    · 难度过低/无需工具/答案泄露/无法加载/答案模糊 → 拒收

REJECT = 会被买方退回(必须修);WARN = 人工复核(自动判不准的项,如难度)。
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# 买方 §3 白名单(14 域名)· 超出即 REJECT
ALLOWED_DOMAINS = frozenset({
    "conda.anaconda.org", "repo.anaconda.com", "ncbi.nlm.nih.gov",
    "ftp.ncbi.nlm.nih.gov", "ensembl.org", "ftp.ensembl.org",
    "hgdownload.soe.ucsc.edu", "uniprot.org", "bioconductor.org",
    "pypi.org", "bioconda.github.io", "cran.r-project.org",
    "cran.rstudio.com", "ftp.ebi.ac.uk",
})

REQUIRED_COLS = ("id", "question", "answer_rubric", "allowed_domains", "human_solvable")

# 从 rubric 抽标准答案(供泄露检查)· 覆盖中英两种买方模板写法
_ANSWER_PATTERNS = (
    r"[Tt]he answer is\s+(.+?)(?:\.|\s+Score|\s*$)",
    r"预期答案为\s*\[?(.+?)\]?(?:。|，|,|\s+若|\s*$)",
    r"answer[:：]\s*(.+?)(?:\.|。|\s*$)",
)

# 难度过低的启发式红旗(买方 §4:<5min / 一次简单聚合 = 拒)
_LOW_DIFFICULTY_HINTS = (
    "how many rows", "count the", "sum of", "average of", "what is the mean",
    "多少行", "求和", "平均值", "计数",
)
# 提示"需工具"的正向信号(缺失→WARN,可能无工具)
_TOOL_SIGNALS = (
    "blast", "align", "annotat", "variant", "genome", "phylogen", "ncbi",
    "ensembl", "uniprot", "bioconductor", "samtools", "bcftools", "bwa",
    "assembl", "quantif", "expression", "database", "reference genome",
    "比对", "注释", "系统发育", "数据库",
)


@dataclass
class Finding:
    row_id: str
    level: str   # REJECT | WARN
    code: str
    msg: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    n_rows: int = 0

    @property
    def rejects(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "REJECT"]

    @property
    def warns(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "WARN"]

    @property
    def passed(self) -> bool:
        return not self.rejects


def extract_reference_answer(rubric: str) -> str | None:
    """从 rubric 抽出标准答案短语(用于泄露检查)。抽不到→None(触发 WARN)。"""
    for pat in _ANSWER_PATTERNS:
        m = re.search(pat, rubric, re.IGNORECASE)
        if m:
            return m.group(1).strip().strip("[]。.，, ")
    return None


def _answer_tokens(answer: str) -> list[str]:
    """把答案拆成有意义的检查词元(过滤短词/停用词),含别名(/ 分隔)。"""
    parts = re.split(r"[\/,;、]| or | 或 ", answer)
    toks: list[str] = []
    for p in parts:
        p = p.strip()
        # 保留 ≥4 字符的实义词(GBM 这类缩写单独保留)
        for w in re.findall(r"[A-Za-z0-9一-鿿]+", p):
            if len(w) >= 4 or (w.isupper() and len(w) >= 2):
                toks.append(w.lower())
    return toks


def check_leakage(row_id: str, question: str, answer: str,
                  data_names: list[str]) -> list[Finding]:
    """买方 §3/§5 红线:答案不得出现在 question / id / 文件名 / 元数据。"""
    out: list[Finding] = []
    haystacks = {
        "question": question.lower(),
        "id": row_id.lower(),
        "filenames": " ".join(data_names).lower(),
    }
    for tok in _answer_tokens(answer):
        for where, hay in haystacks.items():
            if re.search(r"\b" + re.escape(tok) + r"\b", hay):
                out.append(Finding(
                    row_id, "REJECT", "answer_leak",
                    f"标准答案词 '{tok}' 泄露在 {where} 中(买方 §3 红线,自动退)",
                ))
    return out


def validate_row(row: dict, data_dir: Path | None) -> list[Finding]:
    rid = (row.get("id") or "").strip()
    out: list[Finding] = []

    # --- §3 必填列 ---
    for col in REQUIRED_COLS:
        if not (row.get(col) or "").strip():
            out.append(Finding(rid or "<no-id>", "REJECT", "missing_field",
                               f"缺必填列 '{col}'"))
    if not rid:
        return out  # 无 id 后续无从检查

    question = (row.get("question") or "").strip()
    rubric = (row.get("answer_rubric") or "").strip()
    domains_raw = (row.get("allowed_domains") or "").strip()
    solvable = (row.get("human_solvable") or "").strip().lower()

    # --- §4 human_solvable=yes ---
    if solvable and solvable not in ("yes", "y", "true"):
        out.append(Finding(rid, "REJECT", "not_human_solvable",
                           f"human_solvable={solvable!r}(买方仅收 yes)"))

    # --- §3 allowed_domains ⊆ 白名单 ---
    domains = {d.strip() for d in re.split(r"[,\s]+", domains_raw) if d.strip()}
    illegal = domains - ALLOWED_DOMAINS
    if illegal:
        out.append(Finding(rid, "REJECT", "domain_not_allowed",
                           f"域名超出白名单:{sorted(illegal)}"))

    # --- §4 全对全错 rubric ---
    has_binary = bool(re.search(r"1\.0|1\b.*0\b|全对全错|all.?or.?nothing|no partial|不给予部分",
                                rubric, re.IGNORECASE))
    if rubric and not has_binary:
        out.append(Finding(rid, "WARN", "rubric_not_binary",
                           "rubric 未明确全对全错(1.0/0),买方要求无部分分"))

    # --- §3/§5 答案泄露 ---
    answer = extract_reference_answer(rubric)
    data_names = _data_names_for(rid, data_dir)
    if answer:
        out.extend(check_leakage(rid, question, answer, data_names))
    elif rubric:
        out.append(Finding(rid, "WARN", "no_answer_extracted",
                           "rubric 中抽不到标准答案短语,泄露检查跳过(人工核 §3)"))

    # --- §5 无法加载:data/<ID>.zip 存在且可打开 ---
    if data_dir is not None:
        out.extend(_check_data_package(rid, data_dir))

    # --- §4 难度过低启发式 ---
    ql = question.lower()
    if any(h in ql for h in _LOW_DIFFICULTY_HINTS):
        out.append(Finding(rid, "WARN", "maybe_low_difficulty",
                           "问题含'计数/求和/平均'类措辞,疑一次简单聚合可解(买方 §4 拒<5min)"))
    if question and not any(s in ql for s in _TOOL_SIGNALS):
        out.append(Finding(rid, "WARN", "maybe_no_tool",
                           "问题无明显'需外部工具'信号(BLAST/比对/查库等),核 §4 工具要求"))

    # --- §3 提示词自洽(应提到文件/答案格式)---
    if question and "answer" not in ql and "format" not in ql and "格式" not in question:
        out.append(Finding(rid, "WARN", "no_answer_format",
                           "问题未说明答案格式(买方 §3 要求明确 answer 格式)"))

    return out


def _data_names_for(rid: str, data_dir: Path | None) -> list[str]:
    if data_dir is None:
        return []
    zp = data_dir / f"{rid}.zip"
    if not zp.exists():
        return []
    try:
        with zipfile.ZipFile(zp) as z:
            return z.namelist()
    except Exception:
        return []


def _check_data_package(rid: str, data_dir: Path) -> list[Finding]:
    zp = data_dir / f"{rid}.zip"
    if not zp.exists():
        return [Finding(rid, "REJECT", "missing_data_zip",
                        f"缺 data/{rid}.zip(买方 §3:id 必须匹配压缩包名)")]
    try:
        with zipfile.ZipFile(zp) as z:
            if z.testzip() is not None:
                return [Finding(rid, "REJECT", "corrupt_zip", f"{rid}.zip 损坏")]
            if not z.namelist():
                return [Finding(rid, "REJECT", "empty_zip", f"{rid}.zip 为空")]
    except zipfile.BadZipFile:
        return [Finding(rid, "REJECT", "bad_zip", f"{rid}.zip 非合法 zip")]
    return []


def validate_csv(csv_path: Path, data_dir: Path | None) -> Report:
    rep = Report()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLS if c not in (reader.fieldnames or [])]
        if missing:
            rep.findings.append(Finding("<header>", "REJECT", "missing_columns",
                                        f"CSV 缺列:{missing}"))
        seen: set[str] = set()
        for row in reader:
            rep.n_rows += 1
            rid = (row.get("id") or "").strip()
            if rid and rid in seen:
                rep.findings.append(Finding(rid, "REJECT", "dup_id", "id 重复"))
            seen.add(rid)
            rep.findings.extend(validate_row(row, data_dir))
    return rep


def print_report(rep: Report) -> None:
    print(f"\n=== BioMysteryBench 验证报告 · {rep.n_rows} 题 ===")
    print(f"REJECT {len(rep.rejects)} · WARN {len(rep.warns)}")
    for f in rep.rejects:
        print(f"  ❌ [{f.row_id}] {f.code}: {f.msg}")
    for f in rep.warns:
        print(f"  ⚠️  [{f.row_id}] {f.code}: {f.msg}")
    verdict = "✅ 通过供应商自检(仍需真解验证唯一答案+难度)" if rep.passed \
        else "🔴 有 REJECT,买方会退回,先修"
    print(f"\n{verdict}")


_SELFTEST_ROW = {
    "id": "qes1",
    "question": "What cancer is found in this sequenced dataset? Use BLAST against "
                "ncbi.nlm.nih.gov to identify the sample. Answer with the cancer name.",
    "answer_rubric": "The answer is Glioblastoma Multiforme/GBM. Score 1.0 if the "
                     "model did not cheat AND got the answer correct. Score 0 otherwise.",
    "allowed_domains": "ncbi.nlm.nih.gov, ensembl.org, pypi.org",
    "human_solvable": "yes",
}


def _selftest() -> int:
    rep = Report(n_rows=1)
    rep.findings.extend(validate_row(dict(_SELFTEST_ROW), None))
    print_report(rep)
    # 负例:把答案泄露进 question,必须被抓
    leaky = dict(_SELFTEST_ROW)
    leaky["question"] = "This is a Glioblastoma sample. Confirm the cancer type."
    leak_rep = Report(n_rows=1)
    leak_rep.findings.extend(validate_row(leaky, None))
    leaked = any(f.code == "answer_leak" for f in leak_rep.rejects)
    print(f"\n[selftest] 泄露检测(负例应抓到): {'✅ 抓到' if leaked else '🔴 漏了'}")
    return 0 if (rep.passed and leaked) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="BioMysteryBench 供应商侧验证器")
    ap.add_argument("csv", nargs="?", help="problems.csv 路径")
    ap.add_argument("--data-dir", type=Path, default=None, help="data/<ID>.zip 目录")
    ap.add_argument("--selftest", action="store_true", help="内置样例自检")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.csv:
        ap.error("需要 problems.csv 路径,或用 --selftest")
    rep = validate_csv(Path(args.csv), args.data_dir)
    print_report(rep)
    return 0 if rep.passed else 1


if __name__ == "__main__":
    sys.exit(main())
