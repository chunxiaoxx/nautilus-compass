# -*- coding: utf-8 -*-
"""P3 数据 anonymized snapshot:①1454 语料(项目标识→内容哈希) ②测量工件(本身无敏感,直拷+说明)。
产出:docs/paper3_snapshot/(随论文仓发布)。"""
import hashlib
import json
import re
import shutil
from pathlib import Path

SRC = Path("runtime/verdict_corpus")
OUT = Path("runtime/verification-learning-papers/data/paper3_snapshot")
OUT.mkdir(parents=True, exist_ok=True)

ORG_PATTERNS = [
    re.compile(r"[A-Za-z]:\\+Users\\+chunx\\+[^\"'\s,]+"),
    re.compile(r"/home/\w+/[^\s\"',]+"),
    re.compile(r"C--Users-[A-Za-z0-9-]+"),
    re.compile(r"nautilus[-\w]*"),
    re.compile(r"(?:飞轮|禅心|平台框|日报框)"),
]


def scrub(s: str) -> str:
    for pat in ORG_PATTERNS:
        s = pat.sub(lambda m: "ORG_" + hashlib.sha1(m.group(0).encode()).hexdigest()[:8], s)
    return s


def scrub_obj(o):
    if isinstance(o, str):
        return scrub(o)
    if isinstance(o, list):
        return [scrub_obj(x) for x in o]
    if isinstance(o, dict):
        return {k: scrub_obj(v) for k, v in o.items()}
    return o


# ① 语料三折
n_total = 0
for f in sorted(SRC.glob("split_*.jsonl")):
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    out_rows = [scrub_obj(r) for r in rows]
    n_total += len(out_rows)
    (OUT / f.name).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in out_rows) + "\n", encoding="utf-8")
    print(f"{f.name}: {len(out_rows)} rows scrubbed")

# ② 测量工件(answer_key 已无敏感;measure 数据同样处理)
cv_dir = Path("runtime/typesafe_jev_cvscreen")
for name in ("answer_key.json",):
    src = cv_dir / name
    if src.exists():
        data = json.loads(src.read_text(encoding="utf-8"))
        (OUT / name).write_text(
            json.dumps(scrub_obj(data), ensure_ascii=False, indent=1), encoding="utf-8")
        print(name, "copied+scrubbed")

# README(schema 与复算说明)
(OUT / "README.md").write_text("""# Paper 3 Data Snapshot (anonymized)

## Contents
- `split_{train,dev,test}.jsonl`: 1,454 verdict training corpus, three-fold frozen
  (SHA-16 commitments in the paper). Schema per row: qid, verdict (pass/fail/insufficient_evidence),
  truth_label, label_origin, failure_tag where applicable. Project paths replaced by ORG_<hash8>.
- `answer_key.json`: the external-protocol measurement key (40 seeded synthetic CVs),
  committed before any model call; corpus frozen at sha16 c304f878800b1fcb.

## Recompute
- Classifier readings: retrain per the pre-registered criteria doc; splits are frozen—
  any row order change invalidates the SHA commitments.
- External protocol: requests/responses log accompanies the measurement report;
  generator corpus is public upstream (seeded, regenerable).

## Omitted (with reason)
- Decision dataset (2,053 rows): contains organizational correspondence; the paper releases
  its schema and a 100-row sample pending an organization-approved anonymization pass
  (in progress; will land before camera-ready).
""", encoding="utf-8")
print("README written | total rows:", n_total)
