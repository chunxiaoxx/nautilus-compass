#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XERJ 包逐字终扫器 v1(R364):PR 三件套凭据/PII/schema 三层扫描。

判据(先声明后执行,单次全量,零豁免;判据零放宽):
- FAIL = 任何原始凭据/PII 残留(已知字面量/token/邮箱/IPv4/password 赋值)
  或 schema 破损(json 解析失败/缺键/id 非唯一或非 nst-/failed_attempts 空/
  sanitized 非 True/verdict 出枚举);
- WARN = 内部路径/内部 env 名提及(不计 FAIL,列单供人判);
- 退出码 0 = clean,1 = 有 FAIL;--selftest 自证检测力(合成样例必须全命中)。
幂等:PR 日复跑同判据,或凭 sha 不变沿用既有报告。
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PR_DIR = ROOT / "runtime/xerj_pack/pr_ready"
TRIO = ["agent-session-trajectories.jsonl", "README.md", "recipe.toml"]

FAIL_PATTERNS = [
    ("known-secret-literal-1", re.compile(r"iefe4Eey")),
    ("known-secret-literal-2", re.compile(r"Coh9ech3")),
    ("token", re.compile(r"\b(?:sk|hf|ghp|gho|ghs|xoxb|AKID)_[A-Za-z0-9]{20,}\b")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@(?:gmail|outlook|qq|163)\.com")),
    ("raw-ipv4", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
    ("password-assign", re.compile(r"(?i)password\s*[=:]\s*\S+")),
]
WARN_PATTERNS = [
    ("internal-path", re.compile(r"\.claude[\\/]|\.cache[\\/]|/root/|/home/\w+")),
    ("internal-env-name", re.compile(r"a100_env|cloud_permanent|\.ark_env")),
]
REQUIRED_KEYS = ["id", "session_date", "task_topic", "context", "attempted",
                 "failed_attempts", "final_fix", "verdict", "sources", "sanitized"]
VERDICTS = {"pass", "fail", "partial"}
SELFTEST = [
    ("iefe4Eey", "known-secret-literal-1"),
    ("hf_" + "a" * 24, "token"),
    ("someone123@gmail.com", "email"),
    ("10.0.0.5", "raw-ipv4"),
    ("password=hunter2", "password-assign"),
]


def scan_text(name: str, text: str, fails: list, warns: list, first_ln: int = 1) -> None:
    for ln, line in enumerate(text.splitlines(), first_ln):
        for tag, pat in FAIL_PATTERNS:
            for m in pat.finditer(line):
                fails.append(f"{name}:{ln} [{tag}] {m.group(0)[:60]}")
        for tag, pat in WARN_PATTERNS:
            for m in pat.finditer(line):
                warns.append(f"{name}:{ln} [{tag}] {m.group(0)[:60]}")


def scan_jsonl(path: Path, fails: list, warns: list) -> Counter:
    topics, ids = Counter(), set()
    for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        where = f"{path.name}:{ln}"
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            fails.append(f"{where} [schema] json 解析失败: {e}")
            continue
        missing = [k for k in REQUIRED_KEYS if k not in rec]
        if missing:
            fails.append(f"{where} [schema] 缺键 {missing}")
            continue
        if not str(rec["id"]).startswith("nst-"):
            fails.append(f"{where} [schema] id 非 nst- 前缀: {rec['id']}")
        if rec["id"] in ids:
            fails.append(f"{where} [schema] id 重复: {rec['id']}")
        ids.add(rec["id"])
        if not rec["failed_attempts"]:
            fails.append(f"{where} [schema] failed_attempts 为空")
        if rec["sanitized"] is not True:
            fails.append(f"{where} [schema] sanitized 非 True")
        if rec["verdict"] not in VERDICTS:
            fails.append(f"{where} [schema] verdict 出枚举: {rec['verdict']}")
        topics[rec["task_topic"]] += 1
        scan_text(path.name, line, fails, warns, first_ln=ln)
    print(f"records={len(ids)} | topics={dict(topics)}")
    return topics


def run_selftest() -> int:
    misses = []
    for sample, want in SELFTEST:
        hits = [tag for tag, pat in FAIL_PATTERNS if pat.search(sample)]
        if want not in hits:
            misses.append(f"{sample[:24]}!={want}(hits={hits})")
    print("SELFTEST: " + ("PASS 5/5" if not misses else "FAIL " + "; ".join(misses)))
    return 1 if misses else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest()
    fails, warns = [], []
    for fname in TRIO:
        path = PR_DIR / fname
        if not path.exists():
            fails.append(f"{fname} [io] 文件缺失")
            continue
        text = path.read_text(encoding="utf-8")
        if fname.endswith(".jsonl"):
            scan_jsonl(path, fails, warns)
        else:
            scan_text(fname, text, fails, warns)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"sha256 {fname} = {digest}")
    for f in fails:
        print(f"FAIL {f}")
    for w in warns[:20]:
        print(f"WARN {w}")
    if len(warns) > 20:
        print(f"WARN ...共 {len(warns)} 条(截断)")
    print(f"FINAL-SCAN: {'CLEAN' if not fails else 'DIRTY'} (fails={len(fails)} warns={len(warns)})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
