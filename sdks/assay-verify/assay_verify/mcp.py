# -*- coding: utf-8 -*-
"""assay-verify 自带 MCP 服务器(stdio JSON-RPC)——验证能力经 MCP 分发。

运行:python -m assay_verify.mcp
任何 MCP 客户端(Claude Code/Desktop/Cursor/Cline…)配置::

    {"mcpServers": {"assay": {"command": "python", "args": ["-m", "assay_verify.mcp"]}}}

即获得工具 `assay_verify`——对任意 (target, sig, pubkey) 一键三态验真。
零第三方依赖。
"""
from __future__ import annotations

import json
import sys

from ._core import AssayResult, verify

PROTOCOL = "2024-11-05"
TOOLS = [{
    "name": "assay_verify",
    "description": "Verify a signed AI artifact (Assay Protocol v0). Returns "
                   "VALID / INVALID / MALFORMED with sha256 anchor.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "path to the target file"},
            "sig": {"type": "string", "description": "path to the .sig file"},
            "pubkey": {"type": "string", "description": "verifier public key (hex)"},
            "payload_json": {"type": "string",
                             "description": "optional canonical payload JSON "
                                            "(default: wall scorecard format)"},
        },
        "required": ["target", "sig", "pubkey"],
    },
}]


def _result(r: AssayResult) -> dict:
    return {"content": [{"type": "text",
                         "text": json.dumps(
                             {"ok": r.ok, "detail": r.detail, "target": r.target,
                              "sha256": r.sha256}, ensure_ascii=False)}]}


def _handle(method: str, params: dict) -> dict:
    if method == "initialize":
        return {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
                "serverInfo": {"name": "assay-verify", "version": "0.1.0"}}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        args = params.get("arguments", {})
        payload = None
        if args.get("payload_json"):
            payload = json.loads(args["payload_json"])
        return _result(verify(args["target"], args["sig"], args["pubkey"],
                              payload=payload))
    raise ValueError(f"unknown method: {method}")


def serve(stdin=sys.stdin.buffer, stdout=sys.stdout.buffer) -> None:
    """极简 MCP stdio 循环:Content-Length 分帧 JSON-RPC。"""
    while True:
        line = stdin.readline()
        if not line:
            break
        text = line.decode("utf-8", "replace").strip()
        if not text.startswith("{"):
            continue
        try:
            msg = json.loads(text)
            out = {"jsonrpc": "2.0", "id": msg.get("id"),
                   "result": _handle(msg.get("method", ""), msg.get("params", {}) or {})}
        except Exception as e:  # noqa: BLE001 — 错误也走 JSON-RPC
            out = {"jsonrpc": "2.0", "id": msg.get("id") if isinstance(msg, dict) else None,
                   "error": {"code": -32603, "message": str(e)}}
        stdout.write((json.dumps(out, ensure_ascii=False) + "\n").encode("utf-8"))
        stdout.flush()


if __name__ == "__main__":
    serve()
