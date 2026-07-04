# -*- coding: utf-8 -*-
"""hook_template.py - 给 4 dialog 各生成定制 hook(改 EXPECTED_CWD + ALLOWED_ROOT)

复用 compass/ops/auto_surface_hook.py 的模式
"""
import os
import sys
from pathlib import Path

DIALOGS = {
    "v5":     r"C:\Users\chunx\Projects\nautilus-v5",
    "core":   r"C:\Users\chunx\Projects\nautilus-core",
    "buyer":  r"C:\Users\chunx\Projects\nautilus-compass-buyer-tasks",
    "expert": r"C:\Users\chunx\Projects\nautilus-compass-expert-settle",
}


def gen_session_start(dialog_name: str, dialog_root: str) -> str:
    """返 dialog 专属 SessionStart hook 源码。"""
    project_name = dialog_root.rstrip("\\").split("\\")[-1]
    return (
        "# -*- coding: utf-8 -*-\n"
        '"""\n'
        f"{dialog_name} SessionStart hook - 核 cwd + 3 档 alert\n\n"
        f"从 compass/ops/compass_session_start.py 复制 + 改 EXPECTED_CWD\n"
        f"EXPECTED_CWD = {project_name!r}\n"
        '"""\n'
        "import json\n"
        "import os\n"
        "import sys\n\n"
        f'EXPECTED_CWD = "{project_name}"\n'
        f"PROJECT_ROOT = Path(r\"{dialog_root}\")\n\n"
        "ALERTS_RED = [\n"
        f'    "超红: 越界写非 {dialog_name} 项目文件",\n'
        '    "超红: 不写 .claude/memory/session_*.md 就 Stop",\n'
        '    "超红: drift score < -0.07(R1 立停)",\n'
        "]\n"
        "ALERTS_YELLOW = [\n"
        '    "黄: 不读 auto_surface_hook / 不读 NEW_SESSION_START / 不核身份",\n'
        "    \"黄: 段落超 8 行 / '真'字 >= 3\",\n"
        '    "黄: 不写 session memory 落档",\n'
        "]\n\n"
        "def main():\n"
        "    try:\n"
        "        data = json.load(sys.stdin)\n"
        "    except Exception:\n"
        "        data = {}\n"
        "    cwd = data.get(\"cwd\", os.getcwd())\n"
        "    if EXPECTED_CWD not in cwd:\n"
        '        sys.stderr.write("[" + EXPECTED_CWD + "-hook] FAIL: cwd=" + cwd + " 不含 " + EXPECTED_CWD + chr(92) + "n")\n'
        "        return 1\n"
        "    for a in ALERTS_RED:\n"
        '        sys.stderr.write("[" + EXPECTED_CWD + "-alert] [超红] " + a + chr(92) + "n")\n'
        "    for a in ALERTS_YELLOW:\n"
        '        sys.stderr.write("[" + EXPECTED_CWD + "-alert] [黄] " + a + chr(92) + "n")\n'
        "    return 0\n\n"
        'if __name__ == "__main__":\n'
        "    sys.exit(main())\n"
    )


def gen_post_tool(dialog_name: str, dialog_root: str) -> str:
    """返 dialog 专属 PostToolUse hook 源码。"""
    return (
        "# -*- coding: utf-8 -*-\n"
        '"""\n'
        f"{dialog_name} PostToolUse hook - 验越界 + 防冒充\n\n"
        f"从 compass/ops/compass_post_tool.py 复制 + 改 ALLOWED_ROOT\n"
        '"""\n'
        "import json\n"
        "import re\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        f"ALLOWED_ROOT = Path(r\"{dialog_root}\")\n\n"
        "# 禁止其他 dialog 写 OUTBOUND(只允许本 dialog)\n"
        f'FORBIDDEN = re.compile(r"_OUTBOUND_FROM_(?!{dialog_name.upper()}_)", re.IGNORECASE)\n\n'
        "def main():\n"
        "    try:\n"
        "        data = json.load(sys.stdin)\n"
        "    except Exception:\n"
        "        return 0\n"
        '    tool = data.get("tool_name", "")\n'
        '    if tool not in ("Write", "Edit", "MultiEdit"):\n'
        "        return 0\n"
        '    tool_input = data.get("tool_input", {}) or {}\n'
        '    file_path = tool_input.get("file_path", "")\n'
        "    if not file_path:\n"
        "        return 0\n"
        "    p = Path(file_path).resolve()\n"
        "    if not str(p).startswith(str(ALLOWED_ROOT)):\n"
        f'        sys.stderr.write("[{dialog_name}-post] FAIL: 越界写 " + file_path + chr(92) + "n")\n'
        "        return 1\n"
        '    name = Path(file_path).name\n'
        "    if FORBIDDEN.search(name):\n"
        f'        sys.stderr.write("[{dialog_name}-post] FAIL: 禁止冒充 pattern=" + FORBIDDEN.pattern + chr(92) + "n")\n'
        "        return 1\n"
        "    return 0\n\n"
        'if __name__ == "__main__":\n'
        "    sys.exit(main())\n"
    )


def main() -> int:
    """给 4 dialog 各写 2 hook(SessionStart + PostToolUse)到 .claude/hooks/。"""
    for name, root in DIALOGS.items():
        p = Path(root) / ".claude" / "hooks"
        p.mkdir(parents=True, exist_ok=True)
        (p / f"{name}_session_start.py").write_text(
            gen_session_start(name, root), encoding="utf-8"
        )
        print(f"OK: {name} session_start hook")
        (p / f"{name}_post_tool.py").write_text(
            gen_post_tool(name, root), encoding="utf-8"
        )
        print(f"OK: {name} post_tool hook")
    return 0


if __name__ == "__main__":
    sys.exit(main())