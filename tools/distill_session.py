# -*- coding: utf-8 -*-
"""会话结束提炼 hook(Stop 挂点)——写入端压缩:会话→session_*.md→入记忆层。
节流:小于阈值的会话跳过;同会话未显著增长跳过;提炼在后台独立进程跑,hook 秒回。
"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MIN_BYTES = 150 * 1024        # 会话低于 150KB 不值得提炼
GROWTH_RATIO = 1.3            # 已提炼过,增长超 30% 才补提炼
HOME = os.path.expanduser("~")
MARKER_DIR = os.path.join(HOME, ".claude", "memory-distill")
WORKER = os.path.join(HOME, "Projects", "nautilus-compass", "tools", "_distill_worker.py")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    tp = payload.get("transcript_path") or ""
    cwd = payload.get("cwd") or os.getcwd()
    if not tp or not os.path.isfile(tp):
        return
    size = os.path.getsize(tp)
    if size < MIN_BYTES:
        return

    # 记忆目录:按项目目录名(claude projects 命名:路径替换 _ )
    proj_key = cwd.replace(":", "-").replace("\\", "-").replace("/", "-").replace(" ", "-")
    mem_dir = os.path.join(HOME, ".claude", "projects", proj_key, "memory")
    if not os.path.isdir(mem_dir):
        return

    os.makedirs(MARKER_DIR, exist_ok=True)
    marker = os.path.join(MARKER_DIR, os.path.basename(tp) + ".done")
    if os.path.isfile(marker):
        try:
            prev = int(open(marker).read().strip() or 0)
            if size < prev * GROWTH_RATIO:
                return  # 已提炼且无明显新增
        except Exception:
            pass

    # 后台独立进程,hook 立即返回(不阻塞会话收尾)
    subprocess.Popen(
        [sys.executable, WORKER, tp, mem_dir, marker, str(size)],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    main()
