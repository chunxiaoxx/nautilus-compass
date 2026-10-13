#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORG-FUEL 语料 → RAG 记忆层转换器(R536 · P2 收口处置)。

2970 条自产语料(STRONGMODEL_RELABEL_P2_VERDICT 判定:不作 SFT 标签,转 RAG 检索层)
逐条转 memory md(frontmatter 带 pf_id/source/strongmodel_verdict 弱信号),
部署到云端 daemon 扫描的项目目录 orgfuel-corpus/memory/。

用法: python tools/orgfuel_to_memory.py            # 生成 runtime/memory_corpus/orgfuel/
      python tools/orgfuel_to_memory.py --deploy   # 生成+推送云端+触发索引
"""
import json
import sys
from pathlib import Path

OUT = Path("runtime/memory_corpus/orgfuel")
MAX_BODY = 800


def entries():
    rows = [json.loads(l) for l in open("runtime/verdict_corpus/orgfuel_v2/split_train.jsonl",
                                        encoding="utf-8")] + \
           [json.loads(l) for l in open("runtime/verdict_corpus/orgfuel_v2/split_dev.jsonl",
                                        encoding="utf-8")]
    org = [r for r in rows if not r.get("_src", "").startswith(("split_", "delta:"))]
    return org


def slug(qid: str) -> str:
    import hashlib
    h = hashlib.sha256(qid.encode()).hexdigest()[:10]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in qid)[:40]
    return f"orgfuel-{safe}-{h}"


def to_md(r):
    a = r.get("artifact") or {}
    content = ""
    for k in ("content", "situation", "question", "response"):
        v = a.get(k)
        if v and str(v).strip():
            content = str(v)
            break
    if not content.strip():
        content = json.dumps(a, ensure_ascii=False)
    content = content.strip()[:MAX_BODY]
    sm = r.get("strongmodel_verdict", "")
    sm_clean = sm if sm in ("pass", "fail", "insufficient_evidence") else "unparsed"
    name = slug(r["id"])
    sit = (r.get("criteria_ref") or content[:60]).replace("\n", " ")[:80]
    fm = (f"---\n"
          f"name: {name}\n"
          f"description: \"{sit}\"\n"
          f"metadata:\n"
          f"  type: reference\n"
          f"  source: {r['_src']}\n"
          f"  pf_id: {r['id']}\n"
          f"  corpus: orgfuel-v2\n"
          f"  sm_verdict: {sm_clean}\n"
          f"---\n\n")
    return name, fm + content + "\n"


def main():
    deploy = "--deploy" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for r in entries():
        if not (r.get("artifact") or {}):
            continue
        name, md = to_md(r)
        (OUT / f"{name}.md").write_text(md, encoding="utf-8")
        n += 1
    print(f"[OK] {n} md files -> {OUT}")
    if not deploy:
        print("next: python tools/orgfuel_to_memory.py --deploy")
        return
    import subprocess
    subprocess.run(["tar", "-C", str(OUT.parent), "-czf", str(OUT.parent / "orgfuel.tgz"),
                    "orgfuel"], check=True)
    subprocess.run(["scp", "-o", "ConnectTimeout=15", str(OUT.parent / "orgfuel.tgz"),
                    "cloud:/tmp/orgfuel.tgz"], check=True)
    cmd = ("mkdir -p /home/ubuntu/.claude/projects/orgfuel-corpus/memory && "
           "tar -xzf /tmp/orgfuel.tgz -C /home/ubuntu/.claude/projects/orgfuel-corpus/memory "
           "--strip-components=1 && "
           "ls /home/ubuntu/.claude/projects/orgfuel-corpus/memory | wc -l && "
           "rm /tmp/orgfuel.tgz")
    subprocess.run(["ssh", "-o", "ConnectTimeout=15", "cloud", cmd], check=True)
    print("[OK] deployed. daemon inotify will pick up; query with scope=user project=orgfuel-corpus")


if __name__ == "__main__":
    main()
