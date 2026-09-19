# -*- coding: utf-8 -*-
"""MCP stdio 服务器测试:initialize → tools/list → tools/call(真成绩单)往返。"""
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assay_verify import mcp  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def _rpc(server_in, server_out, method, params=None, id_=1):
    server_in.write((json.dumps({"jsonrpc": "2.0", "id": id_,
                                 "method": method, "params": params or {}}) + "\n").encode("utf-8"))
    server_in.seek(0)
    mcp.serve(server_in, server_out)
    server_out.seek(0)
    return json.loads(server_out.readline().decode("utf-8"))


def test_mcp_roundtrip_real_scorecard():
    stdin, stdout = io.BytesIO(), io.BytesIO()
    r1 = _rpc(stdin, stdout, "initialize")
    assert r1["result"]["serverInfo"]["name"] == "assay-verify"

    stdin, stdout = io.BytesIO(), io.BytesIO()
    r2 = _rpc(stdin, stdout, "tools/list")
    assert r2["result"]["tools"][0]["name"] == "assay_verify"

    pub = (ROOT / ".verifypack" / "compass.pub").read_text(encoding="utf-8").strip()
    t = ROOT / "docs" / "wall" / "EXAM5_SCORECARD.md"
    s = ROOT / "docs" / "wall" / "EXAM5_SCORECARD.sig"
    stdin, stdout = io.BytesIO(), io.BytesIO()
    r3 = _rpc(stdin, stdout, "tools/call", {"arguments": {
        "target": str(t), "sig": str(s), "pubkey": pub}})
    text = r3["result"]["content"][0]["text"]
    assert json.loads(text)["detail"] == "VALID"
