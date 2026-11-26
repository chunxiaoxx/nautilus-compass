#!/usr/bin/env python3
"""~/.claude.json 的 zhipu-web-search MCP:改用套餐(Coding Plan)key + 请求头鉴权。

为什么(2026-11-26 实测):
  - 本机给它配的是另一个 key,以 ?Authorization= 查询参数传递 → 服务端回
    -429 {"code":"1113","message":"余额不足或无可用资源包,请充值"}。
  - 智谱官方文档(coding-plan/mcp/search-mcp-server):该 MCP 必须用套餐 key,
    HTTP 方式以请求头 Authorization: Bearer <key> 传入;额度走套餐积分
    (每次调用 1.2 积分,受每 5 小时/每周上限约束),不扣账户余额。
  - 套餐 key 就是 ~/.claude/settings.json 里 Claude Code 正在用的 ANTHROPIC_AUTH_TOKEN(本脚本只比对、只搬运,不打印)。

⚠ 何时跑:~/.claude.json 会被存活中的 Claude Code 窗口在退出时整文件回写,
   所以要**关掉所有 Claude Code 窗口之后**再跑(跑完再开)。幂等,可重复执行。
用法:python ops/apply_zhipu_search_mcp.py [--dry-run]
"""
import argparse
import json
import os
import pathlib
import shutil
import sys
import time

SERVER = "zhipu-web-search"
URL = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    home = pathlib.Path.home()
    claude_path = home / ".claude.json"
    plan_key = (json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8"))
                .get("env") or {}).get("ANTHROPIC_AUTH_TOKEN") or ""
    if not plan_key:
        print(json.dumps({"ok": False, "reason": "plan key not found in settings.json env"}, ensure_ascii=False))
        return 2
    data = json.loads(claude_path.read_text(encoding="utf-8"))
    servers = dict(data.get("mcpServers") or {})
    current = servers.get(SERVER) or {}
    desired = {"type": "http", "url": URL, "headers": {"Authorization": "Bearer " + plan_key}}
    summary = {"server": SERVER, "current_has_url": bool(current.get("url")),
               "current_uses_header": bool((current.get("headers") or {}).get("Authorization")),
               "already_applied": current.get("url") == URL and bool((current.get("headers") or {}).get("Authorization"))}
    print(json.dumps(summary, ensure_ascii=False))
    if args.dry_run or summary["already_applied"]:
        return 0
    backup = home / (".claude.json.bak-" + time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(claude_path, backup)
    servers[SERVER] = desired
    updated = dict(data)
    updated["mcpServers"] = servers
    tmp = home / ".claude.json.tmp"
    tmp.write_text(json.dumps(updated, indent=2, ensure_ascii=False), encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))  # 回读校验:坏文件不替换
    os.replace(tmp, claude_path)
    print(json.dumps({"applied": True, "backup": backup.name}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
