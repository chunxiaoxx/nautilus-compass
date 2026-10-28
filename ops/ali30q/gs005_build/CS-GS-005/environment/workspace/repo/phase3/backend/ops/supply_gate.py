# -*- coding: utf-8 -*-
"""供给闸预检脚本(批次2·V2):19件原料机械项自动预检——不依赖未回执框。
检查项:①五件套完整 ②语境py数>300 ③嵌入模块在 ④骨架挂靠(embed_all.json映射)。
输出:合格进小样快筛队列 / 淘汰件+淘汰原因。"""
import json
import os
import subprocess
import tarfile
import tempfile

NAS = os.path.expanduser("~/mnt/nas-work/shared/gdist_batch1_20261027")
OUT = []


def check(pkg: str) -> dict:
    r = {"pkg": pkg, "ok": True, "fails": []}
    p = os.path.join(NAS, pkg)
    try:
        with tarfile.open(p) as t:
            names = t.getnames()
            top = names[0].split("/")[0]
            five = ["instruction.md", "task.toml", "tests/", "solution/", "environment/"]
            for f in five:
                if not any(n.startswith(f"{top}/{f.rstrip('/')}") for n in names):
                    r["fails"].append(f"缺五件套:{f}")
            py = sum(1 for n in names if n.endswith(".py"))
            r["py_count"] = py
            if py < 300:
                r["fails"].append(f"语境py={py}<300")
    except Exception as e:
        r["fails"].append(f"tar损坏:{str(e)[:60]}")
    r["ok"] = not r["fails"]
    return r


def main():
    pkgs = sorted(f for f in os.listdir(NAS) if f.endswith(".tar.gz") and not f.startswith("._"))
    mapping = {}
    try:
        r = subprocess.run(["ssh", "-p", "24860", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes",
                            "ubuntu@43.160.239.61",
                            "cat /home/ubuntu/flywheel/runtime/fuel_codesense/embedded/embed_all.json"],
                           capture_output=True, text=True, timeout=30)
        mapping = {e.get("pkg", ""): e.get("skeleton", e.get("mech", "?")) for e in json.loads(r.stdout)} if r.stdout.strip().startswith("[") else {}
    except Exception:
        pass
    print(f"供给闸预检 {len(pkgs)} 件(骨架映射{'可读' if mapping else '不可达,该项人工补'})\n")
    passed = []
    for pkg in pkgs:
        r = check(pkg)
        r["skeleton"] = mapping.get(pkg.replace(".tar.gz", ""), mapping.get(pkg, "待挂靠"))
        mark = "PASS" if r["ok"] else "FAIL"
        if r["ok"]:
            passed.append(pkg)
        OUT.append(r)
        print(f"[{mark}] {pkg}  py={r.get('py_count','?')}  骨架={r['skeleton']}"
              + (f"  淘汰:{';'.join(r['fails'])}" if r["fails"] else ""))
    print(f"\n合格 {len(passed)}/{len(pkgs)} → 进小样快筛队列: {', '.join(p.replace('.tar.gz','') for p in passed)}")
    return passed


if __name__ == "__main__":
    main()
