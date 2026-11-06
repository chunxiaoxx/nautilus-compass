#!/usr/bin/env python3
"""把蒸馏生产形态(叙事md+锚点sidecar)发布进 compass memory 目录→recall 可达。

幂等: memory/ 已有同名文件即跳过。tier=episodic+decay(新陈代谢纪律:会话纪要是情景记忆,
按 Ebbinghaus 衰减,访问续命)。增量通道在 J1 闸过后调用本件,形成完整闭环。
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

MEMORY_DIR = Path.home() / ".claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory"


def one_line(narrative: str) -> str:
    """从叙事正文提一行主题(首个非标题非空行,截 60 字)。"""
    for line in narrative.splitlines():
        s = line.strip().lstrip("#-• *").strip()
        if len(s) >= 12 and not s.startswith("源:") and not s.startswith("生成:"):
            return s[:60]
    return "会话蒸馏纪要"


def publish_one(md: Path, anchors: Path) -> bool:
    name = f"distill-{md.stem[:8]}"
    dest = MEMORY_DIR / f"{name}-{time.strftime('%Y%m%d')}.md"
    if dest.exists() or any(MEMORY_DIR.glob(f"{name}-*")):
        return False
    narrative = md.read_text(encoding="utf-8", errors="replace").strip()
    anchor_lines = [l for l in anchors.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    body = (
        "---\n"
        f"name: {name}\n"
        f'description: "蒸馏纪要 {md.stem[:8]}: {one_line(narrative)}"\n'
        "metadata:\n"
        "  node_type: memory\n"
        "  type: project\n"
        "  tier: episodic\n"
        "  decay_rate: 0.7\n"
        f"  origin: distill-pilot\n"
        "---\n\n"
        f"{narrative}\n\n"
        f"## 锚点索引({len(anchor_lines)} 条·源文直提)\n"
        + "\n".join(f"- {l}" for l in anchor_lines)
        + f"\n\n(生产形态正本: runtime/scratch_distill_pilot_20261104/summaries_9b_prod/{md.stem}.md)\n"
    )
    dest.write_text(body, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prod-dir", default="runtime/scratch_distill_pilot_20261104/summaries_9b_prod")
    parser.add_argument("--only", default="", help="只发布指定 session_id(增量通道用)")
    args = parser.parse_args()
    prod = Path(args.prod_dir)
    only = {x for x in args.only.split(",") if x}
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for md in sorted(prod.glob("*.md")):
        if only and md.stem not in only:
            continue
        anchors = prod / f"{md.stem}.anchors.txt"
        if not anchors.exists():
            continue
        if publish_one(md, anchors):
            n += 1
            print(f"[pub] {md.stem[:8]}", file=sys.stderr)
    print(f"published {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
