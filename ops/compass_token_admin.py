#!/usr/bin/env python3
"""compass token 管理工具 · 签发权收敛（2026-08-28 安全修复）

背景：quickstart 曾允许任何能 `ssh cloud` 的进程自签全库 token（无 scope、
无审计、无过期）。本工具把签发/撤销收敛为人工显式操作：

  # 列出全部 token（脱敏 + scope）
  python3 ops/compass_token_admin.py list

  # 签发 scoped token（必须显式给 scope，不给就拒绝——防"顺手全权"）
  python3 ops/compass_token_admin.py grant workbuddy \
      --scopes read:C--Users-chunx,write:WorkBuddy-verify

  # 全权 token（read:*）需要 --yes-i-want-star 显式确认
  python3 ops/compass_token_admin.py grant my-agent --scopes read:* --yes-i-want-star

  # 撤销
  python3 ops/compass_token_admin.py revoke cmp_xxx

  # 一键清理孤儿（名字含 __ 或从未使用过的——保守起见先 list 人工确认）
  python3 ops/compass_token_admin.py revoke cmp_a cmp_b ...

Scope 语法: read:<project> | write:<project> | read:* | write:* | admin
在云端跑（tokens.json 在 /etc/compass/tokens.json，需 sudo；本机测试用
COMPASS_TOKENS_FILE 覆盖路径）。改完须 `sudo systemctl restart compass-mcp-http
compass-mcp-tcp`（服务不热加载）。
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_TOKENS_FILE = "/etc/compass/tokens.json"
VALID_SCOPE_PREFIXES = ("read:", "write:")
FULL_SCOPES = {"read:*", "write:*", "admin"}


def load() -> dict:
    path = os.environ.get("COMPASS_TOKENS_FILE", DEFAULT_TOKENS_FILE)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(d: dict) -> None:
    path = os.environ.get("COMPASS_TOKENS_FILE", DEFAULT_TOKENS_FILE)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, path)
    print(f"written {path} ({len(d)} tokens) — 记得重启: "
          f"sudo systemctl restart compass-mcp-http compass-mcp-tcp")


def parse_scopes(raw: str) -> list[str]:
    out = []
    for s in raw.split(","):
        s = s.strip()
        if not s:
            continue
        if s in FULL_SCOPES:
            out.append(s)
        elif any(s.startswith(p) and len(s) > len(p) for p in VALID_SCOPE_PREFIXES):
            out.append(s)
        else:
            raise SystemExit(f"非法 scope: '{s}'（合法: read:<proj>, write:<proj>, "
                             f"read:*, write:*, admin）")
    if not out:
        raise SystemExit("必须给 --scopes（不给 scope 的签发会被拒绝——"
                         "这就是这次要修的洞）")
    return out


def cmd_list(d: dict) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"tokens.json · {len(d)} 条 · 预览 {now}\n")
    for tok, val in sorted(d.items()):
        scopes = val.get("scopes") if isinstance(val, dict) else (
            ["read:*", "write:*(旧格式)"] if val else [])
        name = tok.split("__")[0] if "__" in tok else tok[:18]
        print(f"  {tok[:14]}…{tok[-6:]}  agent={name:<28} scopes={scopes}")


def cmd_grant(d: dict, agent: str, scopes_raw: str, star_ok: bool) -> None:
    scopes = parse_scopes(scopes_raw)
    if ("read:*" in scopes or "write:*" in scopes or "admin" in scopes) and not star_ok:
        raise SystemExit("全权 scope 需要显式 --yes-i-want-star 确认")
    token = f"cmp_{agent}__{secrets.token_hex(16)}"
    d[token] = {"scopes": scopes,
                "granted_at": datetime.now(timezone.utc).isoformat()}
    save(d)
    print(f"\n新 token（只显示这一次，存好）:\n  {token}\n  scopes: {scopes}")


def cmd_revoke(d: dict, tokens: list[str]) -> None:
    missing = [t for t in tokens if t not in d]
    if missing:
        raise SystemExit(f"不存在: {missing}")
    for t in tokens:
        del d[t]
        print(f"revoked {t[:20]}…")
    save(d)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    g = sub.add_parser("grant")
    g.add_argument("agent")
    g.add_argument("--scopes", required=True)
    g.add_argument("--yes-i-want-star", action="store_true")
    r = sub.add_parser("revoke")
    r.add_argument("tokens", nargs="+")
    a = p.parse_args()
    d = load()
    if a.cmd == "list":
        cmd_list(d)
    elif a.cmd == "grant":
        cmd_grant(d, a.agent, a.scopes, a.yes_i_want_star)
    elif a.cmd == "revoke":
        cmd_revoke(d, a.tokens)


if __name__ == "__main__":
    main()
