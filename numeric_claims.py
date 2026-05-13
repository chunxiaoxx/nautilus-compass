"""v1.7 #2 · numeric_claims 反幻觉 hook

写入时 extract(session_md) 把文里 "N entries / X% / N agents / N files" 存 jsonl
recall 时 cross_ref(query) 如 query 含数字 · 去 jsonl 找同 entity 的不同旧数值
输出 alert 嵌 recall 顶部 · "数字冲突: 你 Nd 前说 X · 现在说 Y"

设计原则 ·
  · 零依赖 (纯正则 + stdlib)
  · 失败静默 (hook 绝不阻塞 session)
  · jsonl append-only · 不改不删 · 审计留痕
"""
import json
import re
import time
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "compass"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CLAIMS_FILE = CACHE_DIR / "numeric_claims.jsonl"

# Patterns · anchor-keyword + numeric value
# 保守 · 只抓高价值 entity · 避免抓到版本号 / 日期等噪音
PATTERNS = [
    # 数字 + entity (forward · 自由文本主流序)
    (re.compile(r"(\d[\d,]*)\s*entries\b", re.I), "entries"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*%\s*(?:recall|准确率|drop|降|覆盖率|accuracy)", re.I), "percentage"),
    (re.compile(r"(\d+)\s*agents?\b", re.I), "agents"),
    (re.compile(r"(\d+)\s*tools?\b(?!kit)", re.I), "tools"),
    (re.compile(r"port\s*(\d{4,5})\b", re.I), "port"),
    (re.compile(r"(\d{4,5})\s*port\b", re.I), "port"),
    # v1.5.2 #2 · entity + 数字 (reverse · frontmatter / list 形式)
    (re.compile(r"\bentries\s*[:=]?\s*(\d[\d,]*)\b", re.I), "entries"),
    (re.compile(r"\bagents?\s*[:=]?\s*(\d+)\b", re.I), "agents"),
    (re.compile(r"\btools?\s*[:=]?\s*(\d+)\b(?!kit)", re.I), "tools"),
]


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _parse_seed_block(text: str) -> list[dict]:
    """v1.5.2 #2 · extract numeric_claims_seed from yaml frontmatter.

    yaml list of strings like:
      - "v1.5.1 entries 56"
      - "anchors pos 28"
    runs PATTERNS over each string · returns matched claims.
    Avoids requiring PyYAML · regex extraction works for our 1-level list.
    """
    out = []
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return out
    fm = m.group(1)
    seed_re = re.compile(r"numeric_claims_seed\s*:\s*\n((?:\s+-\s+.*\n?)+)", re.M)
    sm = seed_re.search(fm)
    if not sm:
        return out
    for line in sm.group(1).splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        item = line.lstrip("- ").strip().strip("\"'")
        if item:
            out.extend(extract_from_text(item))
    return out


def extract_from_text(text: str) -> list[dict]:
    """Return list of {entity, value, raw_match}."""
    out = []
    for pat, entity in PATTERNS:
        for m in pat.finditer(text):
            raw = m.group(1).replace(",", "")
            try:
                val = float(raw) if "." in raw else int(raw)
            except ValueError:
                continue
            out.append({"entity": entity, "value": val, "span": m.group(0)[:60]})
    return out


def append_claims(source_file: str, claims: list[dict]) -> int:
    """Append claims to jsonl · return n written."""
    if not claims:
        return 0
    ts = int(time.time())
    n = 0
    with CLAIMS_FILE.open("a", encoding="utf-8") as fp:
        for c in claims:
            rec = {
                "ts": ts,
                "source": source_file,
                "entity": c["entity"],
                "value": c["value"],
                "span": c["span"],
            }
            fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def cross_ref(query: str, lookback_days: int = 14) -> list[str]:
    """Return alert lines · [] if no conflict.

    Extract numeric claims from query · compare with jsonl history for same entity
    · if latest past value != query value · return alert.
    """
    if not CLAIMS_FILE.exists():
        return []
    q_claims = extract_from_text(query)
    if not q_claims:
        return []
    cutoff = time.time() - lookback_days * 86400
    history: dict[str, list[dict]] = {}
    try:
        with CLAIMS_FILE.open("r", encoding="utf-8") as fp:
            for line in fp:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec["ts"] < cutoff:
                    continue
                history.setdefault(rec["entity"], []).append(rec)
    except Exception:
        return []
    alerts = []
    for qc in q_claims:
        past = history.get(qc["entity"], [])
        if not past:
            continue
        # find most recent past value that differs
        past_sorted = sorted(past, key=lambda r: -r["ts"])
        for rec in past_sorted:
            if rec["value"] != qc["value"]:
                days_ago = (time.time() - rec["ts"]) / 86400
                alerts.append(
                    f"[!] 数字冲突 [{qc['entity']}] · {days_ago:.1f}d 前你说 {rec['value']} "
                    f"· 现在说 {qc['value']} · 来源: {Path(rec['source']).name}"
                )
                break
    return alerts


def already_ingested(source_file: str) -> bool:
    """v1.5.2 #1 · True if CLAIMS_FILE already has any record from this source.

    Used by stop_hook to skip re-ingest on daily 24h glob.
    """
    if not CLAIMS_FILE.exists():
        return False
    try:
        with CLAIMS_FILE.open("r", encoding="utf-8") as fp:
            for line in fp:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("source") == source_file:
                    return True
    except Exception:
        return False
    return False


def ingest_session_file(path: Path) -> int:
    """Extract + append · used by stop_hook."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    # v1.5.2 #2 · frontmatter seed 优先 + 反向 regex 全文 · 合并去重
    seed_claims = _parse_seed_block(text)
    body_claims = extract_from_text(text)
    seen = set()
    merged = []
    for c in seed_claims + body_claims:
        key = (c["entity"], c["value"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(c)
    return append_claims(str(path), merged)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 自测
        sample = "767 → 56 entries · 降 92.7% recall · 6 agents · port 9877 · 16 tools"
        claims = extract_from_text(sample)
        print(f"extracted {len(claims)}:")
        for c in claims:
            print(f"  · {c}")
        n = append_claims("test_sample", claims)
        print(f"wrote {n}")
        alerts = cross_ref("now we have 9999 entries and 100 agents")
        print(f"cross_ref alerts: {len(alerts)}")
        for a in alerts:
            print(f"  {a}")
    else:
        print("usage: numeric_claims.py test")
