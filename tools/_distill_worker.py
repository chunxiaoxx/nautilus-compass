# -*- coding: utf-8 -*-
"""提炼 worker(后台):transcript jsonl → claude -p 蒸馏 → memory/session_*.md。
教训吸收:子进程 claude 需清代理+显式模型(bc1-launch-eve);输出必须非空校验(防假绿)。
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WINDOW_CHARS = 40000          # 送蒸馏的窗口(尾部)
MAX_FIRST_USER = 1500         # 首条用户消息截断
TIMEOUT_S = 600


def find_claude():
    """claude CLI 定位:PATH → Mac nvm bin(claude=happy 别名,子进程不可见)→ npm 全局(Windows .cmd 需经 cmd.exe)。"""
    p = shutil.which("claude")
    if p:
        return p
    # 2026-10-20 Mac 适配:Mac 上 claude 是 happy 的 shell 别名,子进程 which 不到;
    # happy 兼容 -p --model 等参数(实测 haiku 蒸馏通路 OK)。扫 nvm bin 下实体。
    import glob as _g
    for _pat in ("~/.nvm/versions/node/*/bin/claude", "~/.nvm/versions/node/*/bin/happy"):
        _hits = _g.glob(os.path.expanduser(_pat))
        if _hits:
            return _hits[0]
    cand = os.path.join(os.environ.get("APPDATA", ""), "npm", "claude.cmd")
    if os.path.isfile(cand):
        return cand
    return "claude"


def extract(transcript_path):
    """取首条用户消息 + 尾部窗口的对话文本。"""
    first_user = ""
    tail = []
    total = 0
    with open(transcript_path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for line in lines:
        try:
            j = json.loads(line)
        except Exception:
            continue
        msg = j.get("message") or {}
        role = msg.get("role") or j.get("type")
        content = msg.get("content")
        if role == "user" and not first_user:
            text = content if isinstance(content, str) else " ".join(
                c.get("text", "") for c in content if isinstance(c, dict))
            if text.strip() and "system-reminder" not in text[:100]:
                first_user = text.strip()[:MAX_FIRST_USER]
        if role in ("user", "assistant"):
            text = content if isinstance(content, str) else " ".join(
                c.get("text", "") for c in (content or []) if isinstance(c, dict) and c.get("type") == "text")
            if text.strip():
                tail.append(f"【{role}】{text.strip()}")
                total += len(text)
    window = "\n\n".join(tail)[-WINDOW_CHARS:]
    return first_user, window


def slugify(text):
    words = re.findall(r"[一-鿿A-Za-z0-9]+", text[:120])
    s = "-".join(words[:4])
    return re.sub(r"[^0-9A-Za-z一-鿿-]", "", s)[:28] or "session"


PROMPT = """你是会话档案蒸馏器。以下是一段 Claude Code 会话的首条用户消息与尾部对话。
蒸馏成一篇记忆档案(md),只保留对未来工作有用:决策(含依据)、bug 与根修、技法/配方、教训、待办。丢弃寒暄/过程性叙述/自夸。
格式要求:
- 首行: # <8-15字标题>
- 然后 3-8 条要点(每条 ≤60字,结论先行,数字/路径/commit号保留)
- 末行: "来源: <今日日期> 会话蒸馏(自动)"
- 总长 ≤600字,中文,直接输出 md 正文,不要解释。

首条用户消息:
{first}

尾部对话:
{window}
"""


def main():
    tp, mem_dir, marker, size = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    first, window = extract(tp)
    if len(window) < 400:
        return
    prompt = PROMPT.format(first=first, window=window)
    env = {k: v for k, v in os.environ.items()
           if not k.lower().endswith("_proxy") and k not in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")}
    claude = find_claude()
    argv = [claude, "-p", "--model", "haiku", "--max-turns", "1"]
    if claude.lower().endswith((".cmd", ".bat")):
        argv = ["cmd.exe", "/c"] + argv
    # 2026-10-20 Mac:nvm bin 里的 node 脚本(happy)shebang 靠 PATH 找 node,
    # hook/ssh 环境 PATH 可能无 nvm → claude 所在目录前置进子进程 PATH(实测 RC=127 根因)
    env["PATH"] = os.path.dirname(os.path.abspath(claude)) + os.pathsep + env.get("PATH", "")
    # 2026-10-20 Mac 第二坑:happy -p 的 SDK 路径不解析 --model 参数(传什么都走
    # settings 默认 glm-5.3[1M],该后缀原生 claude 不认→unrecognized→max-turns 空转)。
    # worker 自带蒸馏模型 env 覆盖(k3-256k=haiku 档;COMPASS_DISTILL_MODEL 可换),不动用户 settings。
    _dm = os.environ.get("COMPASS_DISTILL_MODEL", "k3-256k")
    for _k in ("ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
               "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL"):
        env[_k] = _dm
    try:
        # 提示词走 stdin(40k 窗口超 Windows 32k 命令行上限)
        r = subprocess.run(argv, input=prompt, capture_output=True,
                           text=True, timeout=TIMEOUT_S, env=env,
                           encoding="utf-8", errors="replace")
        out = (r.stdout or "").strip()
    except Exception:
        return
    # 假绿防护:太短或含道歉/失败语视为失败
    if len(out) < 120 or out.startswith(("(失败", "I'm sorry", "抱歉")):
        return
    body = out if out.startswith("#") else "# 会话蒸馏\n\n" + out
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    name = f"session_auto_{ts}_{slugify(first)}.md"
    path = os.path.join(mem_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\nfact_status: inferred\ndistilled: auto\n---\n\n" + body + "\n")
    with open(marker, "w") as f:
        f.write(str(size))


if __name__ == "__main__":
    main()
