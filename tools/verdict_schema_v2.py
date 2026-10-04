#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verdict Schema v2 validator+migrator(docs/protocol/VERDICT_SCHEMA_V2.md)。

3.3.0 起正本在 assay/schema_v2.py(nautilus_compass.assay 包内同源文件);
本 CLI 用 importlib 直载该文件,零环境依赖(repo 内直跑,无需 pip 安装)。
用法:
  python tools/verdict_schema_v2.py validate <verdict.json>
  python tools/verdict_schema_v2.py migrate  <verdict.json> [--out out_v2.json]
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_SPEC = importlib.util.spec_from_file_location(
    "compass_assay_schema_v2",
    Path(__file__).resolve().parent.parent / "assay" / "schema_v2.py")
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)
migrate, validate = _mod.migrate, _mod.validate


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd, src = sys.argv[1], Path(sys.argv[2])
    v = json.loads(src.read_text(encoding="utf-8"))
    if cmd == "validate":
        errors, warns = validate(v)
        print(json.dumps({"file": src.name, "errors": errors, "warnings": warns,
                          "compliant": not errors}, ensure_ascii=False, indent=1))
        return 0 if not errors else 1
    if cmd == "migrate":
        out = migrate(v)
        dst = src.with_name(src.stem + "_v2.json")
        dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        errors, warns = validate(out)
        print(json.dumps({"migrated_to": str(dst), "post_errors": errors,
                          "post_warnings": warns, "compliant": not errors},
                         ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
