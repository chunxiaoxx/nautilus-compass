# -*- coding: utf-8 -*-
"""通用隐藏启动器 · nautilus-compass 副本 · 2026-10-25 治弹窗，2026-10-26 治控制台委托。

与 nautilus-v5\\scripts\\_hidden_run.py 同源（stdlib only）。

核心要点（2026-10-26 实测修正）
--------------------------------
`CREATE_NO_WINDOW` 是**反效果**：它让子进程拿不到控制台句柄 → ssh/cmd 自己
AllocConsole() 新建一个**正常可见**的控制台 → Windows Terminal 委托接管 → 新 tab
抢焦点（标题 = exe 完整路径）。

实测 ssh 自建的 conhost 子进程数：
    CREATE_NO_WINDOW             -> 1 个(可见)  => 会弹 tab
    继承父控制台(creationflags=0) -> 0 个        => 不弹
    CREATE_NEW_CONSOLE + SW_HIDE -> 1 个(隐藏)  => 不弹

所以：
    父进程有控制台  -> 继承（不传 creationflags）
    父进程无控制台  -> CREATE_NEW_CONSOLE + STARTUPINFO(SW_HIDE)
"""
import os
import subprocess
import sys

CREATE_NEW_CONSOLE = 0x00000010


def _comspec() -> str:
    return os.environ.get("COMSPEC") or "C:\\Windows\\System32\\cmd.exe"


def _has_console() -> bool:
    try:
        import ctypes
        return ctypes.windll.kernel32.GetConsoleWindow() != 0
    except Exception:
        return False


def _child_kwargs() -> dict:
    if _has_console():
        return {}
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    return {"creationflags": CREATE_NEW_CONSOLE, "startupinfo": si}


def _open_out(path: str, append: bool, cwd: str | None = None):
    if not path or path.lower() == "nul":
        return subprocess.DEVNULL
    if cwd and not os.path.isabs(path):
        path = os.path.join(cwd, path)
    mode = "ab" if append else "wb"
    try:
        return open(path, mode)
    except Exception:
        return subprocess.DEVNULL


def main() -> int:
    argv_in = sys.argv[1:]
    cwd = None
    out_path = None
    out_append = True

    i = 0
    while i < len(argv_in):
        a = argv_in[i]
        if a == "--cwd":
            i += 1
            cwd = argv_in[i] if i < len(argv_in) else None
        elif a == "--out":
            i += 1
            out_path = argv_in[i] if i < len(argv_in) else None
            out_append = True
        elif a == "--outnew":
            i += 1
            out_path = argv_in[i] if i < len(argv_in) else None
            out_append = False
        elif a == "--":
            i += 1
            break
        else:
            break
        i += 1

    prog = argv_in[i:]
    if not prog:
        return 2

    if prog[0].lower().endswith((".cmd", ".bat")):
        prog = [_comspec(), "/c"] + prog

    try:
        subprocess.Popen(
            prog,
            cwd=cwd or None,
            stdin=subprocess.DEVNULL,
            stdout=_open_out(out_path, out_append, cwd),
            stderr=subprocess.STDOUT,
            **_child_kwargs()
        )
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
