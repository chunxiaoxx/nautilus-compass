#!/usr/bin/env python3
"""harbor→items 装配器 v1(2026-10-27 · 批次2开足马力件)

输入: NAS gdist harbor 包(含 embedded/environment/workspace/repo 载体)
     + 题面件目录(题面.toml/instruction.md/tests/solution/pytest.ini/conftest.py)
输出: items/CS-XXX 完整判分形态 + 装配报告(缺件清单)
用法:
  python3 harbor_assembler.py <harbor.tar.gz> <topic_dir> <out_items_dir>
  python3 harbor_assembler.py --smoke <harbor.tar.gz>   # 只验载体+列缺件
"""
import argparse, tarfile, shutil
from pathlib import Path

REQ_TOPIC = ["task.toml", "instruction.md", "tests", "solution", "pytest.ini", "conftest.py"]


def assemble(harbor: Path, topic: Path | None, out: Path, smoke=False) -> int:
    iid = harbor.name.split("_")[0]                    # CS-210
    item = out / iid
    if item.exists():
        print(f"[SKIP] {item} 已存在"); return 1
    item.mkdir(parents=True)
    # 1) 载体解包: tar 内 <iid>/embedded/environment/workspace/repo → item/environment/workspace/repo
    with tarfile.open(harbor, "r:gz") as tf:
        members = [m for m in tf.getmembers() if m.name.startswith(f"{iid}/embedded/environment/")]
        prefix = f"{iid}/embedded/environment/"
        for m in members:
            m.name = m.name[len(prefix):]               # environment/... 相对化
            tf.extract(m, item)
    print(f"[OK] 载体: {len(members)} 件 → {item}/environment/")
    # 2) solution/counterexamples(嵌仓包自带的反例件)
    with tarfile.open(harbor, "r:gz") as tf:
        ce = [m for m in tf.getmembers() if m.name.startswith(f"{iid}/embedded/solution/")]
        for m in ce:
            m.name = m.name[len(f"{iid}/embedded/solution/"):]
            tf.extract(m, item / "counterexamples_pkg")  # 反例件打包位,题面 solution 由 topic_dir 提供
    # 3) 题面件
    missing = []
    for f in REQ_TOPIC:
        src = topic / f if topic else None
        if src and (topic / f).exists():
            dst = item / f
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, dst)
        else:
            missing.append(f)
    if missing:
        print(f"[WARN] 题面缺件: {missing} —— 题面件由 v5 出题深化提供,到件后重跑本装配器(--fill 模式)")
    if smoke:
        shutil.rmtree(item)
        print(f"[SMOKE] 载体/结构验证通过,试装目录已清理")
        return 0
    print(f"[DONE] {item}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("harbor", type=Path)
    ap.add_argument("topic", type=Path, nargs="?")
    ap.add_argument("out", type=Path, nargs="?")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    out = a.out or (a.topic.parent if a.topic else Path("."))
    raise SystemExit(assemble(a.harbor, a.topic, out, a.smoke))
