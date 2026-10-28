"""全批附件 PII 扫描:身份证/手机号/银行卡模式,机械可复跑。"""
import re, sys
from pathlib import Path
from collections import defaultdict
import pandas as pd

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
P_ID = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
P_MOBILE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
P_BANK = re.compile(r"(?<!\d)\d{15,19}(?!\d)")

def scan_text(t, hits):
    ids = P_ID.findall(t)
    hits["身份证"] += len(ids)
    masked = P_ID.sub("", t)
    hits["手机号"] += len(P_MOBILE.findall(masked))
    masked2 = P_MOBILE.sub("", masked)
    hits["卡号/长数字"] += len(P_BANK.findall(masked2))

def scan_xlsx(p, hits):
    try:
        for sn, df in pd.read_excel(p, sheet_name=None, header=None).items():
            for col in df.columns:
                for v in df[col].dropna().astype(str):
                    if len(v) >= 11: scan_text(v, hits)
    except Exception as e:
        hits["读取失败"] += 1

def scan_docx(p, hits):
    try:
        import zipfile
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
        scan_text(re.sub(r"<[^>]+>", " ", xml), hits)
    except Exception:
        hits["读取失败"] += 1

results = {}
for f in ROOT.rglob("*"):
    if f.suffix.lower() not in (".xlsx", ".xls", ".docx") or f.name.startswith("~$"):
        continue
    # 归属人 = 路径中第一个像人名的目录段(粗略:取含中文的最深父目录链)
    owner = "/".join(f.relative_to(ROOT).parts[:2])
    hits = defaultdict(int)
    (scan_xlsx if f.suffix.lower() in (".xlsx", ".xls") else scan_docx)(f, hits)
    if any(v for k, v in hits.items() if k != "读取失败"):
        key = str(f.relative_to(ROOT))
        results[key] = dict(hits)

total = defaultdict(int)
print(f"扫描完成,含 PII 的文件 {len(results)} 个:")
for k, v in sorted(results.items(), key=lambda x: -sum(x[1].values()))[:30]:
    line = " ".join(f"{a}×{b}" for a, b in v.items())
    print(f"  {k[:90]} → {line}")
    for a, b in v.items(): total[a] += b
print("\n合计:", dict(total))
