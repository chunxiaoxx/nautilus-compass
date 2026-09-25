# -*- coding: utf-8 -*-
"""对拍考题生成:110 记忆文档 × 2 查询(cn 口语/en 关键词),MiniMax-M3。
生成即冻结 queries.json(含语料 sha256),判分只认冻结版(PREREGISTER 判据)。
用法:MINIMAX_API_KEY=... python gen_queries.py"""
import hashlib
import json
import os
import re
import time
import urllib.request
from pathlib import Path

MEMDIR = (Path.home() / ".claude/projects"
          / "C--Users-chunx-Projects-nautilus-compass/memory")
OUT = Path(__file__).parent / "queries.json"
BASE = "https://api.minimaxi.com/v1"
KEY = os.environ.get("MINIMAX_API_KEY") or SystemExit("set MINIMAX_API_KEY")

PROMPT = """以下是一条 AI 组织记忆档案(标题+正文截断)。

---
标题:{name}
正文:{body}
---

假设你是这个组织的成员,几周后你模糊了记忆,想检索找回这条档案。
生成两条你会输入的检索查询:
1. q_cn:中文口语回忆式,如"之前那个XX问题最后怎么处理的来着"——
   模拟真实模糊回忆,不要照抄标题,保留关键线索词
2. q_en:英文关键词式,如"mailbox outage root cause 893"

严格只输出 JSON:{{"q_cn": "...", "q_en": "..."}}"""


def chat(user: str) -> str:
    body = json.dumps({"model": "MiniMax-M3", "temperature": 0,
                       "max_tokens": 2048,
                       "messages": [{"role": "user", "content": user}]
                       }).encode()
    for i in range(3):
        try:
            req = urllib.request.Request(
                BASE + "/chat/completions", data=body,
                headers={"Authorization": f"Bearer {KEY}",
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)["choices"][0]["message"]["content"]
        except Exception:
            if i == 2:
                raise
            time.sleep(2 ** (i + 1))


def parse_q(text: str):
    t = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"\{.*\}", t, flags=re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return {"q_cn": str(d["q_cn"]), "q_en": str(d["q_en"])}
    except Exception:
        return None


def main():
    docs = {}
    for f in sorted(MEMDIR.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        docs[f.name] = f.read_text(encoding="utf-8")[:4000]
    corpus_sha = hashlib.sha256(
        json.dumps(docs, sort_keys=True).encode()).hexdigest()
    print(f"corpus: {len(docs)} docs, sha256={corpus_sha[:16]}")

    queries, failed = [], []
    for i, (name, body) in enumerate(docs.items()):
        try:
            q = parse_q(chat(PROMPT.format(name=name, body=body[:2500])))
        except Exception as e:
            q = None
            print(f"[{i+1}/{len(docs)}] {name} ERR {repr(e)[:120]}")
        if q:
            queries.append({"doc": name, **q})
            print(f"[{i+1}/{len(docs)}] {name} ok", flush=True)
        else:
            failed.append(name)
    OUT.write_text(json.dumps({
        "corpus_sha256": corpus_sha, "n_docs": len(docs),
        "failed": failed, "queries": queries},
        ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    qsha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"frozen: {len(queries)} queries, failed={len(failed)}, "
          f"queries.sha256={qsha[:16]}")


if __name__ == "__main__":
    main()
