"""soul 工具箱(U19 · 2026-09-26 用户令:调用/搜索/compass 整合/深度分析全开)。

四件,全部 fail-open(工具坏=返回空/soul 不停轮,守护 daemon 稳定优先):
- compass_call 系:组织记忆库读写。MCP 无状态直调(实测:无需 initialize
  握手,POST /mcp/ + Bearer token 即应答;compass 3.1.0,token 热载)。
- web_search:duckduckgo html(通用网页)+ gh search code(GitHub 代码域)双引擎。
- second_opinion:换强模型(glm-5.3)独立复审胜选提案——深度分析层。

本模块属 soul 感官器官,SELF_IMPROVE_EXCLUDE 锁死禁自改(config.py)。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from urllib.parse import unquote

import requests

COMPASS_URL = os.environ.get("COMPASS_MCP_URL", "http://127.0.0.1:8097/mcp/")
COMPASS_TOKEN = os.environ.get("COMPASS_MCP_TOKEN", "")
SECOND_OPINION_MODEL = os.environ.get("SOUL_SECOND_OPINION_MODEL", "glm-5.3")
_TIMEOUT = 25


# --- compass(全平台信息整合) ---


def _parse_mcp_result(status_code: int, content_type: str, body: str):
    """MCP 响应 → {"text": str} | None。兼容 JSON 与 SSE 两种载体;错误→None。"""
    try:
        if "text/event-stream" in (content_type or ""):
            for ln in body.splitlines():
                if ln.startswith("data:"):
                    body = ln[5:].strip()
                    break
        d = json.loads(body)
        if d.get("error") is not None:
            return None
        content = (d.get("result") or {}).get("content") or []
        texts = [c.get("text", "") for c in content if isinstance(c, dict)]
        merged = "\n".join(t for t in texts if t)
        return {"text": merged} if merged else None
    except Exception:  # noqa: BLE001
        return None


def _mcp_call(name: str, args: dict):
    """无状态 tools/call。无 token/网络错/协议错 → None(fail-open)。"""
    if not COMPASS_TOKEN:
        return None
    try:
        r = requests.post(
            COMPASS_URL,
            headers={"Authorization": f"Bearer {COMPASS_TOKEN}",
                     "Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                  "params": {"name": name, "arguments": args}},
            timeout=_TIMEOUT)
        return _parse_mcp_result(r.status_code, r.headers.get("content-type", ""),
                                 r.text)
    except Exception:  # noqa: BLE001
        return None


def compass_recall(query: str, project: str = "nautilus-core", top_k: int = 5) -> str:
    """查组织记忆。返回文本(可能为空)。"""
    r = _mcp_call("recall", {"query": query, "project": project, "top_k": top_k})
    return (r or {}).get("text", "")[:2000]


def compass_ingest(name: str, description: str, body: str,
                   project: str = "nautilus-core") -> bool:
    """写组织记忆(schema:name 8-15 字标题必填/description ≤200/body 全文)。"""
    return _mcp_call("ingest_obs", {
        "name": name[:40], "description": description[:200],
        "body": body[:4000], "project": project}) is not None


# --- 全网搜索(双引擎) ---


def _parse_ddg(html: str) -> list:
    """duckduckgo lite 结果页 → [(title, url, snippet)]。纯函数可测。
    9/26 实测:主站 html/ 反爬空页,lite 版可用(GET,table 布局)。"""
    from html import unescape as _unescape
    out = []
    for m in re.finditer(
            r'class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
            r'(?:.*?class="result-snippet"[^>]*>(.*?)</)', html, re.S):
        url, title, snip = m.groups()
        url = _unescape(url)                       # &amp; → &(先实体还原再截)
        url = re.sub(r'&rut=.*$', '', unquote(re.sub(r'^.*uddg=', '', url)))
        strip = lambda s: re.sub(r'<[^>]+>', '', _unescape(s)).strip()  # noqa: E731
        out.append((strip(title), url, strip(snip or "")))
    return out


def web_search(query: str, n: int = 5) -> str:
    """双引擎:ddg lite(通用网页;主站反爬,lite 实测可用)→ gh api search/code
    (GitHub 域;云上 gh 版本老无 search 子命令,走 gh api)。
    返回参考文本(可能为空)。"""
    try:
        r = requests.get("https://lite.duckduckgo.com/lite/",
                         params={"q": query}, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0 nautilus-soul"})
        items = _parse_ddg(r.text)[:n]
        if items:
            return "\n".join(f"- {t}: {u} — {s[:100]}" for t, u, s in items)
    except Exception:  # noqa: BLE001
        pass
    try:
        r = subprocess.run(
            ["gh", "api", "-X", "GET", "search/code",
             "-f", f"q={query}", "-f", f"per_page={n}",
             "--jq", '.items[] | .repository.full_name + "/" + .path'],
            capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            return "\n".join("- " + ln for ln in r.stdout.splitlines()[:n])
    except Exception:  # noqa: BLE001
        pass
    return ""


# --- 深度分析(second opinion) ---


def _verdict_line(text: str) -> str:
    """评审输出 → 首个 APPROVE/REJECT 行;无 → ''(失败=放行,不阻塞)。"""
    for ln in (text or "").splitlines():
        s = ln.strip()
        if s.startswith(("APPROVE", "REJECT")):
            return s
    return ""


def second_opinion(proposal: str, context: str) -> str:
    """换强模型独立复审自改提案。'APPROVE...'/'REJECT: 理由'/''(失败放行)。"""
    try:
        from agent_engine.llm.client import LLMClient
        c = LLMClient(model=SECOND_OPINION_MODEL)
        r = c.chat(
            "你是独立资深评审(soul 之外的第二意见)。以下是将应用到生产代码的"
            "自改提案与目标文件上下文。严格评估:正确性/副作用/是否最小改动/"
            "会否引入回归。第一行必须是 APPROVE 或 REJECT(REJECT 附一句理由),"
            "总长 ≤200 字。\n\n"
            f"提案:\n{proposal[:3000]}\n\n上下文(节选):\n{context[:4000]}")
        return _verdict_line(r or "")
    except Exception:  # noqa: BLE001
        return ""
