"""compass · liveness framework · 聚合 3 探针 · 验证 PoI binding-DONE 第 3 条(SSOT §3)· 单文件可跑 CLI。

设计=effect 注入(probe_fn)+ 现有 PoI code 复用(不重写逻辑)· anchor #5 不另造。
3 探针对应 SSOT binding-DONE §3 "PoI 账本恢复增长(probe_ledger_growth 从 DORMANT → GREEN)" 拆解:
- probe_ledger_growth:本地 PoI 快照存在 + 行数>0 → GREEN(数据活着)
- probe_snapshot_freshness:快照 mtime < 2h → GREEN(刷新活着)
- probe_impact_axis:patch_v14_recall_poi_boost.py 存在 + 含 poi_impact wiring → GREEN(路径就位)

用法(单文件可跑):
  python ops/liveness_audit.py            # 跑全部
  python ops/liveness_audit.py --probe ledger_growth
  python ops/liveness_audit.py --json     # JSON 输出(给 cron + 监控)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# 复用现有 PoI code · 不重写解析逻辑(anchor #5)
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_REPO))
from proof.poi_credit_store import load_snapshot  # noqa: E402

# 探针默认配置(可被 CLI flag / env 覆盖)
DEFAULT_SNAPSHOT_PATH = Path(
    os.environ.get(
        "COMPASS_POI_CACHE_DIR",
        str(Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache"),
    )
) / "poi_credit_cache.json"
DEFAULT_FRESHNESS_HOURS = 2.0
DEFAULT_MIN_LINES = 1
DEFAULT_PATCH_FILE = _REPO / "ops" / "patch_v14_recall_poi_boost.py"

# 探针名常量(SSOT 命名对齐)
PROBE_LEDGER = "ledger_growth"
PROBE_FRESHNESS = "snapshot_freshness"
PROBE_IMPACT = "impact_axis"
ALL_PROBES = [PROBE_LEDGER, PROBE_FRESHNESS, PROBE_IMPACT]


def _is_green(condition: bool, detail: str) -> dict:
    return {"status": "GREEN" if condition else "RED", "detail": detail}


def probe_ledger_growth(
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    min_lines: int = DEFAULT_MIN_LINES,
) -> dict:
    """PoI 快照存在 + 行数 > min_lines → GREEN(账本活着)。"""
    if not snapshot_path.exists():
        return _is_green(False, f"snapshot missing: {snapshot_path}")
    try:
        snapshot = load_snapshot(snapshot_path)
    except Exception as e:
        return _is_green(False, f"snapshot parse fail: {e}")
    line_count = len(snapshot)
    return _is_green(
        line_count > min_lines,
        f"snapshot lines = {line_count} (threshold > {min_lines})",
    )


def probe_snapshot_freshness(
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    max_age_hours: float = DEFAULT_FRESHNESS_HOURS,
) -> dict:
    """快照 mtime < max_age_hours → GREEN(刷新活着)。"""
    if not snapshot_path.exists():
        return _is_green(False, f"snapshot missing: {snapshot_path}")
    mtime_s = snapshot_path.stat().st_mtime
    age_h = (time.time() - mtime_s) / 3600.0
    return _is_green(
        age_h < max_age_hours,
        f"snapshot age = {age_h:.2f}h (threshold < {max_age_hours}h)",
    )


def probe_impact_axis(patch_file: Path = DEFAULT_PATCH_FILE) -> dict:
    """patch_v14_recall_poi_boost.py 存在 + 含 poi_impact wiring → GREEN(路径就位)。"""
    if not patch_file.exists():
        return _is_green(False, f"patch file missing: {patch_file}")
    try:
        content = patch_file.read_text(encoding="utf-8")
    except Exception as e:
        return _is_green(False, f"patch read fail: {e}")
    has_wiring = "poi_impact" in content
    return _is_green(
        has_wiring,
        f"poi_impact wiring in patch = {has_wiring} (file: {patch_file.name})",
    )


def run_all(
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    max_age_hours: float = DEFAULT_FRESHNESS_HOURS,
    min_lines: int = DEFAULT_MIN_LINES,
    patch_file: Path = DEFAULT_PATCH_FILE,
) -> dict:
    """跑全部探针 → {probe_name: {status, detail}}。"""
    return {
        PROBE_LEDGER: probe_ledger_growth(snapshot_path, min_lines),
        PROBE_FRESHNESS: probe_snapshot_freshness(snapshot_path, max_age_hours),
        PROBE_IMPACT: probe_impact_axis(patch_file),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="compass liveness framework · 聚合 3 探针 · 验证 PoI binding-DONE §3"
    )
    ap.add_argument("--probe", choices=ALL_PROBES, help="单探针跑(默认全部)")
    ap.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    ap.add_argument("--max-age-hours", type=float, default=DEFAULT_FRESHNESS_HOURS)
    ap.add_argument("--min-lines", type=int, default=DEFAULT_MIN_LINES)
    ap.add_argument("--patch", type=Path, default=DEFAULT_PATCH_FILE)
    ap.add_argument("--json", action="store_true", help="JSON 输出(给 cron + 监控)")
    args = ap.parse_args(argv)

    if args.probe:
        fn = {
            PROBE_LEDGER: lambda: probe_ledger_growth(args.snapshot, args.min_lines),
            PROBE_FRESHNESS: lambda: probe_snapshot_freshness(
                args.snapshot, args.max_age_hours
            ),
            PROBE_IMPACT: lambda: probe_impact_axis(args.patch),
        }[args.probe]
        result = {args.probe: fn()}
    else:
        result = run_all(
            args.snapshot, args.max_age_hours, args.min_lines, args.patch
        )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for name, r in result.items():
            print(f"[{r['status']}] {name}: {r['detail']}")

    # 全部 GREEN = exit 0 · 任意 RED = exit 1(给 cron/监控告警)
    return 0 if all(r["status"] == "GREEN" for r in result.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
