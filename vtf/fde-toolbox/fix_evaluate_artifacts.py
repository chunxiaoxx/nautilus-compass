#!/usr/bin/env python3
"""Fix genopt/FDE task evaluate.py so it generates EVERY artifact its
frontier_eval/artifact_files.txt manifest claims.

买方反馈根因(2026-07-07 · 王老师):artifact_files.txt 列 metrics.json +
eval.stdout.txt + eval.stderr.txt,但 evaluate.py 只写 metrics.json、print 到
stdout(不落 eval.stdout.txt)、无人写 eval.stderr.txt → workspace 不可复现 →
削弱 Dockerfile 准确性。系统性:genopt_factory 全部 11 题同 bug(compass 已实测)。

本脚本给 evaluate.py 注入:
  1. `_Tee` 类 → 把 stdout/stderr 复制到 eval.stdout.txt / eval.stderr.txt(与
     metrics.json 同 cwd)。
  2. `_write_artifacts_index()` → 生成 artifacts.json(每个产物 sha256 + 字节数),
     买方可 re-run + re-hash 自证可复现。
  3. main() 包装:tee 装/卸 + 异常 traceback 落 eval.stderr.txt。
幂等(已修的跳过)· stdlib only · 不改评分逻辑(_run_eval 原样)。

用法:
    python fix_evaluate_artifacts.py <task_dir>/verification/evaluate.py [...更多]
    # 批量:
    find genopt_factory/tasks -name evaluate.py -exec python fix_evaluate_artifacts.py {} +
修完记得给每题 frontier_eval/artifact_files.txt 补一行 `artifacts.json`。
"""
import sys

TEE_CLASS = '''

class _Tee:
    """Duplicate a stream to a file so frontier_eval artifacts
    (eval.stdout.txt / eval.stderr.txt) are produced deterministically."""

    def __init__(self, stream, path):
        self._stream = stream
        self._file = open(path, "w", encoding="utf-8")

    def write(self, data):
        self._stream.write(data)
        self._file.write(data)
        return len(data)

    def flush(self):
        self._stream.flush()
        self._file.flush()

    def close(self):
        try:
            self._file.flush()
            self._file.close()
        except Exception:
            pass
'''

INDEX_FN = '''

def _write_artifacts_index():
    """artifacts.json — self-verifying index (sha256 + bytes) of every artifact
    the frontier_eval manifest claims. Best-effort; never raises."""
    import hashlib as _hl
    index = {"generated_by": "verification/evaluate.py", "artifacts": {}}
    for _name in ("metrics.json", "eval.stdout.txt", "eval.stderr.txt"):
        try:
            with open(_name, "rb") as _fh:
                _raw = _fh.read()
            index["artifacts"][_name] = {"sha256": _hl.sha256(_raw).hexdigest(),
                                         "bytes": len(_raw)}
        except OSError:
            index["artifacts"][_name] = {"sha256": None, "bytes": None, "missing": True}
    try:
        with open("artifacts.json", "w", encoding="utf-8") as _fh:
            import json as _json
            _json.dump(index, _fh, indent=2)
    except OSError:
        pass

'''

NEW_MAIN = '''def main():
    # frontier_eval contract: tee stdout/stderr to the manifest artifact files
    # (same cwd as metrics.json), then write artifacts.json index. Reproducible.
    _out_tee = _Tee(sys.__stdout__, "eval.stdout.txt")
    _err_tee = _Tee(sys.__stderr__, "eval.stderr.txt")
    sys.stdout = _out_tee
    sys.stderr = _err_tee
    try:
        _run_eval()
    except Exception:
        import traceback
        traceback.print_exc()
        raise
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        _out_tee.close()
        _err_tee.close()
        _write_artifacts_index()


'''


def patch(path):
    s = open(path, encoding="utf-8").read()
    if "_write_artifacts_index" in s or "_Tee" in s:
        return "already-patched"
    if "\ndef main():\n" not in s:
        return "skip-no-main"
    if "import sys" not in s:
        s = s.replace("import json", "import json\nimport sys", 1) if "import json" in s else "import sys\n" + s
    # insert _Tee after the first import block (before first top-level def)
    first_def = s.index("\ndef ")
    s = s[:first_def] + TEE_CLASS + s[first_def:]
    # rename main -> _run_eval, insert index fn + new main before __main__ guard
    s = s.replace("\ndef main():\n", "\ndef _run_eval():\n", 1)
    guard = 'if __name__ == "__main__":'
    if guard not in s:
        return "skip-no-guard"
    s = s.replace(guard, INDEX_FN + NEW_MAIN + guard, 1)
    open(path, "w", encoding="utf-8").write(s)
    return "patched"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: fix_evaluate_artifacts.py <evaluate.py> [...]")
    for f in sys.argv[1:]:
        print(f"{patch(f)}: {f}")
