"""compass auto-surface hook · 扫 _OUTBOUND_FROM_*_TO_compass_*.md · 注 context。

复用 anchor #5:不重写 hook 架构,只加 scan + watermark + inject 一段。
按 6/17 rootcause 钉死方案 + 6/8 dogfood 双通道(本地文件 = 不靠 MCP)。

env 控:
  COMPASS_AUTO_SURFACE_DIR  · 扫哪个目录(默认 _OUTBOUND 落点)
  COMPASS_DIALOG_NAME       · 本 dialog 名(默认 compass)
  COMPASS_SEEN_FILE         · watermark 落点(默认 .seen_<name>)

退出:stdout 输出 📥 inbound N 条待读(给 session-start context 注入)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DIALOG_NAME = os.environ.get("COMPASS_DIALOG_NAME", "compass")
# 扫多个 dialog 的 _OUTBOUND 落点(不靠 MCP 跨进程)
SCAN_DIRS = [
    Path(os.environ.get("COMPASS_AUTO_SURFACE_DIR",
                        str(Path(__file__).resolve().parent.parent))),
    Path(os.environ.get("COMPASS_AUTO_SURFACE_CORE",
                        str(Path(__file__).resolve().parent.parent.parent / "nautilus-core"))),
    Path(os.environ.get("COMPASS_AUTO_SURFACE_V5",
                        str(Path(__file__).resolve().parent.parent.parent / "nautilus-v5"))),
]
SEEN_FILE = Path(os.environ.get(
    "COMPASS_SEEN_FILE",
    str(Path(__file__).resolve().parent.parent / f".seen_{DIALOG_NAME}"),
))
PATTERN = f"_OUTBOUND_FROM_*_TO_{DIALOG_NAME}_*.md"


def _seen_set() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    return set(SEEN_FILE.read_text(encoding="utf-8").splitlines())


def _save_seen(seen: set[str]) -> None:
    SEEN_FILE.write_text("\n".join(sorted(seen)), encoding="utf-8")


def scan() -> list[Path]:
    """扫 SCAN_DIRS 多路径下 _OUTBOUND_FROM_*_TO_<dialog>_*.md 文件,返回未读列表。"""
    seen = _seen_set()
    files: list[Path] = []
    for d in SCAN_DIRS:
        if d.exists():
            files.extend(sorted(d.glob(PATTERN)))
    return [f for f in files if f.name not in seen]


def main() -> int:
    unseen = scan()
    if not unseen:
        print(f"[in] {DIALOG_NAME} auto-surface: 0 inbound outbounds")
        return 0
    print(f"[in] {DIALOG_NAME} auto-surface: {len(unseen)} inbound outbounds 待读:")
    for f in unseen:
        print(f"  - {f.name}")
    seen = _seen_set()
    seen.update(f.name for f in unseen)
    _save_seen(seen)
    return 0


if __name__ == "__main__":
    sys.exit(main())