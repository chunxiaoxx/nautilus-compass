"""Bounded read-only source inspection; writes only metadata under this directory."""
import hashlib
import fcntl
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / 'SOURCE_CHECKS.json'
PATTERNS = {
    'credential_literal': re.compile(r'''(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|client[_-]?secret|authorization)\s*["']?\s*[:=]\s*["']?([^\s"',;}]{8,})'''),
    'known_token': re.compile(r'(?<![A-Za-z0-9_])(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,}|AKIA[A-Z0-9]{16})'),
    'bearer': re.compile(r'(?i)Bearer\s+[A-Za-z0-9._~+/-]{8,}'),
    'credential_uri': re.compile(r'[A-Za-z][A-Za-z0-9+.-]*://[^\s/:@]+:[^\s@]+@[^\s]+'),
    'connection_string': re.compile(r'(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|rediss)://[^\s]+'),
    'private_key': re.compile(r'-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH PRIVATE KEY)-----'),
    'recall_receipt': re.compile(r'recall_token:\s*\S+'),
}

def inspect(path, max_bytes=2_000_000):
    p = Path(path)
    record = {'path': str(p), 'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'exists': p.exists()}
    if not p.exists():
        save(record)
        return record, '', set()
    st = p.stat()
    record.update(size_bytes=st.st_size, mtime_ns=st.st_mtime_ns, is_file=p.is_file())
    if not p.is_file() or st.st_size > max_bytes:
        record['content_read'] = False
        save(record)
        return record, '', set()
    b = p.read_bytes()
    s = b.decode('utf-8', errors='replace')
    record.update(sha256=hashlib.sha256(b).hexdigest(), normalized_lf_sha256=hashlib.sha256(b.replace(b'\r\n', b'\n').replace(b'\r', b'\n')).hexdigest(), content_read=True)
    secret_lines = set()
    findings = []
    in_key = False
    for n, line in enumerate(s.splitlines(), 1):
        kinds = [kind for kind, pattern in PATTERNS.items() if pattern.search(line)]
        if in_key or 'private_key' in kinds:
            kinds.append('private_key_block')
            in_key = not bool(re.search(r'-----END .*PRIVATE KEY-----', line))
        if kinds:
            secret_lines.add(n)
            findings.append({'line': n, 'kinds': sorted(set(kinds)), 'line_sha256': hashlib.sha256(line.encode()).hexdigest()})
    record.update(sensitive_pattern_present=bool(findings), sensitive_findings=findings, secret_scan_scope='heuristic patterns; not a guarantee of no secrets')
    save(record)
    return record, s, secret_lines

def save(record):
    with (ROOT / 'SOURCE_CHECKS.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}
        data[record['path']] = record
        REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def lines(path, pattern=None, start=None, end=None, limit=70):
    meta, source, blocked = inspect(path)
    print(json.dumps({'metadata': meta}, ensure_ascii=False))
    count = 0
    for n, line in enumerate(source.splitlines(), 1):
        if start is not None and n < start or end is not None and n > end:
            continue
        if pattern and not re.search(pattern, line, re.I):
            continue
        print(f'{n}: ' + ('[SENSITIVE LINE REDACTED; see metadata SHA]' if n in blocked else line))
        count += 1
        if count >= limit:
            break

def json_fields(path, keys):
    meta, source, blocked = inspect(path)
    print(json.dumps({'metadata': meta}, ensure_ascii=False))
    if not source:
        return
    if blocked:
        print('Selected JSON fields withheld; use bounded redacted lines.')
        return
    data = json.loads(source)
    print(json.dumps({k: data.get(k) for k in keys}, ensure_ascii=False, indent=2))
