# -*- coding: utf-8 -*-
"""架构扫描生成器——ARCHITECTURE.md 的机器层(真相源=代码/DB/systemd)。
防"做完就丢":结构数据永远可再生成(本地跑 10 秒),人只维护解读层(ARCHITECTURE.md)。
每日由 frame_snapshot.py 顺带重扫。跑: python ops/gen_architecture.py
"""
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sh(cmd: str, cwd: Path | None = None) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          cwd=cwd or ROOT, timeout=60).stdout or ""


def main() -> None:
    L = [f"# 架构扫描(机器层 · 生成于 {datetime.now():%Y-%m-%d %H:%M})",
         "> 解读/状态标记见 docs/ARCHITECTURE.md;本页纯结构数据,随时再生成。", ""]

    L.append("## API 路由(文件|端点数|prefix)")
    total = 0
    for f in sorted((ROOT / "api").glob("*.py")):
        txt = f.read_text(encoding="utf-8", errors="replace")
        n = len(re.findall(r"@router\.(get|post|put|delete|patch)", txt))
        m = re.search(r'APIRouter\(prefix\s*=\s*["\']([^"\']+)', txt)
        total += n
        if n:
            L.append(f"- {f.name} | {n} | {m.group(1) if m else ''}")
    L.append(f"- **合计 {total} 端点**\n")

    L.append("## 数据表(models)")
    tabs = set()
    for f in (ROOT / "models").glob("*.py"):
        tabs.update(re.findall(r'__tablename__\s*=\s*["\'](\w+)', f.read_text(errors="replace")))
    L.append("- " + " ".join(sorted(tabs)) + f"\n- **合计 {len(tabs)} 表(models 定义;生产存活以 DB 实查为准)**\n")

    L.append("## 工具与运行时")
    L.append("- tools/: " + " ".join(p.name for p in (ROOT / "tools").glob("*.py")))
    L.append("- ops/: " + " ".join(p.name for p in (ROOT / "ops").glob("*.py")))

    L.append("\n## 云运行面(ssh 实测)")
    L.append("- services: " + " ".join(sorted(l.split()[0] for l in sh(
        "ssh -o ConnectTimeout=12 cloud \"systemctl list-units --type=service --state=running --no-legend --no-pager | grep -Ei 'nautilus|compass|flywheel|v5|v7|kairos'\"", ROOT).splitlines() if l.strip())))
    L.append("- timers: " + " ".join(sorted(t for t in sh(
        "ssh -o ConnectTimeout=12 cloud \"systemctl list-timers --all --no-legend --no-pager\"",
        ROOT).split() if t.endswith(".timer"))))
    db = sh("ssh -o ConnectTimeout=12 cloud \"python3 /home/ubuntu/nautilus-mvp/phase3/backend/ops/db_tables.py\"", ROOT)
    tabs_live = set(db.split())
    dead = sorted(tabs - tabs_live)
    L.append(f"- 生产库实存表 {len(tabs_live)} 张;models 定义未上生产 {len(dead)} 张: {' '.join(dead) or '无'}")

    L.append("\n## 各框自报(FRAME.yaml · Backstage 原则:拥有者维护,中心采集)")
    FRAME_PATHS = {
        "flywheel": r"C:\Users\chunx\Projects\nautilusflywheel\FRAME.yaml",
        "v5": r"C:\Users\chunx\nautilus-v5\FRAME.yaml",
        "compass": r"C:\Users\chunx\Projects\nautilus-compass\FRAME.yaml",
        "platform": r"C:\Users\chunx\Projects\nautilus-core\FRAME.yaml",
    }
    for name, p in FRAME_PATHS.items():
        fp = Path(p)
        if fp.exists():
            body = " | ".join(l.strip() for l in fp.read_text(encoding="utf-8").splitlines() if l.strip())
            L.append(f"- {name}: {body[:150]}")
        else:
            L.append(f"- {name}: (FRAME.yaml 未建,函 frame-upgrade-20260904-{name})")

    L += ["", "## 表健康(活性 · 单一真相源 ops/table_health.py)"]
    th = sh("ssh -o ConnectTimeout=12 cloud \"cd /home/ubuntu/nautilus-mvp/phase3/backend "
            "&& python3 ops/table_health.py --exact\"", ROOT)
    th_lines = [l for l in th.strip().splitlines() if l and not l.startswith("JSON: ")]
    L += th_lines or ["- (表健康采集失败:云端 ops/table_health.py 未部署或 ssh 不通)"]

    out = ROOT / "docs" / "evidence" / "org-os" / "pilot" / "architecture_scan.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"written {out} · {total} endpoints · {len(tabs)} models / {len(tabs_live)} live")


if __name__ == "__main__":
    main()
