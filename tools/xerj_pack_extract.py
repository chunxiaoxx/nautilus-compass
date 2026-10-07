#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XERJ 捐赠包抽取器 v0(R319):queue.md 轮次 → agent-session-trajectory 记录 jsonl。
按设计 V1 schema;脱敏第一步(凭据正则),其余四步人工/复扫。"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "runtime/loop/queue.md"
OUT = ROOT / "runtime/xerj_pack/sessions.jsonl"

SECRET_PATTERNS = [
    (re.compile(r'iefe4Eey'), 'REDACTED'), (re.compile(r'Coh9ech3'), 'REDACTED'),
    (re.compile(r'A100_PW_ENV'), 'REDACTED'),
    (re.compile(r'\b[A-Za-z0-9_\-]{16,}@(?:gmail|outlook|qq|163)\.com\b'), 'REDACTED_EMAIL'),
    (re.compile(r'\b(?:sk|hf|ghp|gho|ghs)_[A-Za-z0-9]{20,}\b'), 'REDACTED_TOKEN'),
    (re.compile(r'\b\d{1,3}(?:\.\d{1,3}){3}\b(?::\d{2,5})?'), 'REDACTED_IP'),
    (re.compile(r'password[=:]\s*\S+', re.I), 'password=REDACTED'),
]

TOPIC_RULES = [
    ('infra-diagnosis', ('daemon', 'overload', 'nginx', '404', 'ssh', '隧道', 'GPU 嵌入')),
    ('eval-judging', ('判读', '判据', 'PRECOR', 'E-NACRE', 'FAIL', 'PASS', 'U 态', '复算')),
    ('ledger-audit', ('A1', 'A2', '裁定', '冲正', 'balance', 'NAU', '口径')),
]


def sanitize(text: str) -> str:
    for pat, rep in SECRET_PATTERNS:
        text = pat.sub(rep, text)
    return text


def topic_of(block: str) -> str:
    hits = {t for t, kws in TOPIC_RULES for kw in kws if kw in block}
    for t, _ in TOPIC_RULES:
        if t in hits:
            return t
    return 'ops-misc'


def failures_of(block: str):
    """从轮次文本粗抽失败尝试(fail 词锚段)。"""
    out = []
    for m in re.finditer(r'([^\n]{0,160}?(?:崩|FAIL|红灯|失败|误诊|翻车|坑)[^\n]{0,200})', block):
        out.append({"action": sanitize(m.group(1))[:300], "outcome": "fail",
                    "diag_verbatim": sanitize(m.group(1))[:300]})
    return out[:5]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    q = QUEUE.read_text(encoding='utf-8')
    n = 0
    with open(OUT, 'w', encoding='utf-8') as f:
        for block in re.split(r'\n(?=### R\d+)', q):
            if not block.startswith('### R'):
                continue
            rid = re.search(r'### (R\d+)', block).group(1)
            date = re.search(r'(2026-10-\d\d)', block)
            fails = failures_of(block)
            if not fails:
                continue  # 只收含失败尝试的会话(设计 §三)
            rec = {
                "id": f"nst-{rid.lower()}",
                "session_date": date.group(1) if date else "2026-10-XX",
                "task_topic": topic_of(block),
                "context": "production multi-agent engineering org · watch-loop ops",
                "attempted": fails,
                "failed_attempts": fails,
                "final_fix": {"action": sanitize(block[:200]), "outcome":
                              "pass" if ('修复' in block or '✅' in block) else "partial",
                              "evidence_sha16": hashlib.sha256(block.encode()).hexdigest()[:16]},
                "verdict": "pass" if '✅' in block else ("partial" if '修复' in block else "fail"),
                "sources": [f"queue.md@{rid}"],
                "sanitized": True,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
            n += 1
    from collections import Counter
    topics = Counter(json.loads(l)['task_topic']
                     for l in open(OUT, encoding='utf-8'))
    print(f"records={n} | topics={dict(topics)}")
    print(f"-> {OUT}")


if __name__ == '__main__':
    main()
