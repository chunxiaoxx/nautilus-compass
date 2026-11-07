"""Read only the authorized output directory; never load an array payload."""
import ast
import datetime
import hashlib
import json
import os
import re
import stat
import struct

ROOT = '/root/vdd2/p0_full/out'
LIMIT = 65536
MAX_ENTRIES = 128
consumed = 0
secret_patterns = [
    re.compile(r'(?<![A-Za-z0-9_])(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,}|AKIA[A-Z0-9]{16})'),
    re.compile(r'(?i)Bearer\s+[A-Za-z0-9._~+/-]{8,}'),
    re.compile(r'[A-Za-z][A-Za-z0-9+.-]*://[^\s/:@]+:[^\s@]+@[^\s]+'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'''(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|client[_-]?secret|authorization)\s*["']?\s*[:=]\s*["']?([^\s"',;}]{8,})'''),
]
allowed = {
    'model', 'tag', 'n', 'layer', 'pooling', 'maxlen', 'batch',
    'ids_sha16', 'ids_sha256', 'id_order_sha16', 'id_order_sha256',
    'data', 'data_path', 'data_file', 'input', 'input_file', 'input_path',
    'anchor', 'anchor_path', 'anchor_file', 'anchor_manifest',
    'anchor_sha16', 'anchor_v01_sha16', 'input_sha256', 'data_sha256',
    'manifest', 'manifest_path', 'effect', 'cause', 'F1_zero_fail',
    'schema', 'schema_version', 'ts', 'created_at', 'source', 'files',
    'sha256', 'sha16', 'shas', 'dtype', 'shape', 'dataset',
    'file', 'filename', 'path', 'sec', 'bytes', 'size_bytes',
}


def digest(b):
    return hashlib.sha256(b).hexdigest()


def sensitive(s):
    return any(p.search(s) for p in secret_patterns)


def safe(value, depth=0):
    if depth > 5:
        return '[depth bounded]'
    if isinstance(value, str):
        if sensitive(value) or re.search(r'\b[A-Za-z][A-Za-z0-9+.-]*://', value):
            return {'value_withheld': True, 'value_sha256': digest(value.encode())}
        return value[:1200]
    if isinstance(value, dict):
        return {k: safe(v, depth + 1) for k, v in value.items() if k in allowed}
    if isinstance(value, (list, tuple)):
        return [safe(v, depth + 1) for v in value[:32]]
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return '[type withheld]'


def read_limited(handle, length):
    global consumed
    if length < 0 or length > LIMIT - consumed:
        raise ValueError('metadata_budget_exceeded')
    data = handle.read(length)
    consumed += len(data)
    if len(data) != length:
        raise EOFError('short_metadata_read')
    return data


def open_regular(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError('not_regular_file')
    return os.fdopen(fd, 'rb')


result = {
    'root': ROOT,
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'metadata_budget_bytes': LIMIT,
    'array_payload_bytes_read': 0,
    'recursive_scan': False,
    'symlinks_followed': False,
    'directory_index': [],
    'small_metadata': [],
    'array_headers': [],
}
phase = 'root_lstat'
try:
    root_stat = os.lstat(ROOT)
    result['root_exists'] = True
    if not stat.S_ISDIR(root_stat.st_mode):
        result['status'] = 'ROOT_NOT_REGULAR_DIRECTORY_NO_FOLLOW'
    else:
        phase = 'directory_index'
        entries = []
        iterator = os.scandir(ROOT)
        with iterator:
            for entry in iterator:
                if len(entries) >= MAX_ENTRIES:
                    result['index_truncated'] = True
                    break
                entries.append(entry)
        result.setdefault('index_truncated', False)
        entries.sort(key=lambda e: e.name)
        targets = []
        for entry in entries:
            st = entry.stat(follow_symlinks=False)
            name = safe(entry.name)
            item = {
                'name': name, 'size_bytes': st.st_size,
                'mtime_utc': datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(),
                'mtime_ns': st.st_mtime_ns,
                'kind': 'file' if stat.S_ISREG(st.st_mode) else 'directory' if stat.S_ISDIR(st.st_mode) else 'symlink' if stat.S_ISLNK(st.st_mode) else 'other',
            }
            result['directory_index'].append(item)
            if item['kind'] == 'file' and isinstance(name, str):
                targets.append((entry, st))

        # NPY headers have priority over JSON within the one shared 64 KiB budget.
        for entry, st in targets:
            if not entry.name.endswith('.npy'):
                continue
            item = {'file': entry.name, 'file_size_bytes': st.st_size, 'full_array_sha256_computed': False}
            try:
                with open_regular(entry.path) as handle:
                    prefix = read_limited(handle, 8)
                    if prefix[:6] != b'\x93NUMPY':
                        raise ValueError('not_npy')
                    major, minor = prefix[6], prefix[7]
                    if major not in (1, 2, 3):
                        raise ValueError('unsupported_npy_version')
                    length_bytes = read_limited(handle, 2 if major == 1 else 4)
                    length = struct.unpack('<H' if major == 1 else '<I', length_bytes)[0]
                    if length > 16384:
                        raise ValueError('header_size_limit')
                    header = read_limited(handle, length)
                    parsed = ast.literal_eval(header.decode('latin1' if major < 3 else 'utf-8'))
                    after = os.fstat(handle.fileno())
                item.update(
                    status='HEADER_READ_SUCCESS', npy_version=[major, minor],
                    header_bytes=len(prefix) + len(length_bytes) + len(header),
                    header_sha256=digest(prefix + length_bytes + header),
                    shape=safe(parsed['shape']), descr=safe(parsed['descr']),
                    fortran_order=bool(parsed['fortran_order']),
                    stable_size_mtime=(st.st_size == after.st_size and st.st_mtime_ns == after.st_mtime_ns),
                )
            except Exception as error:
                item.update(status='HEADER_UNVERIFIED', error_type=type(error).__name__)
            result['array_headers'].append(item)

        for entry, st in targets:
            if not entry.name.endswith('.json') or not (entry.name.startswith('meta_') or 'manifest' in entry.name.lower()):
                continue
            item = {'file': entry.name, 'size_bytes': st.st_size}
            if st.st_size > LIMIT - consumed:
                item['status'] = 'SKIPPED_METADATA_BUDGET'
                result['small_metadata'].append(item)
                continue
            try:
                with open_regular(entry.path) as handle:
                    raw = read_limited(handle, st.st_size)
                    after = os.fstat(handle.fileno())
                text = raw.decode('utf-8-sig')
                findings = []
                for number, line in enumerate(text.splitlines(), 1):
                    if sensitive(line):
                        findings.append({'line': number, 'line_sha256': digest(line.encode())})
                parsed = json.loads(text)
                item.update(
                    status='SMALL_METADATA_READ_SUCCESS', sha256=digest(raw),
                    top_level_keys=[safe(k) for k in parsed] if isinstance(parsed, dict) else [],
                    safe_fields=safe(parsed), sensitive_pattern_findings=findings,
                    stable_size_mtime=(st.st_size == after.st_size and st.st_mtime_ns == after.st_mtime_ns),
                )
            except Exception as error:
                item.update(status='METADATA_UNVERIFIED', error_type=type(error).__name__)
            result['small_metadata'].append(item)
        result['status'] = 'DIRECTORY_METADATA_READ_SUCCESS'
except FileNotFoundError:
    if phase == 'root_lstat':
        result.update(status='AUTHORIZED_ROOT_NOT_FOUND', root_exists=False)
    else:
        result.update(status='DIRECTORY_CHANGED_OR_FILE_MISSING', error_type='FileNotFoundError')
except Exception as error:
    result.update(status='REMOTE_READ_FAILED', error_type=type(error).__name__, errno=getattr(error, 'errno', None))
result['metadata_bytes_read'] = consumed
print(json.dumps(result, ensure_ascii=False))
