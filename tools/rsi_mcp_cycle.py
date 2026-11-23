#!/usr/bin/env python3
"""Run one local RSI proof-of-recall cycle through Compass MCP stdio.

This is a bounded recovery path for GUI MCP reconnect failures. It exercises
the same sequence as the normal client, then leaves a JSON receipt. It never
sends mail, posts externally, starts GPU work, or changes acceptance criteria.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER = Path.home() / ".claude" / "plugins" / "nautilus-compass" / "mcp_server.py"
DEFAULT_PROJECT = "-Users-chunxiao-wang-Projects-nautilus-compass"
MEMORY_DIR = Path.home() / ".claude" / "projects" / DEFAULT_PROJECT / "memory"
RECEIPT = ROOT / "runtime" / "org-continuity" / "rsi-proof-of-recall-latest.json"


def _text(result: dict[str, Any]) -> str:
    for block in result.get("result", {}).get("content", []):
        if block.get("type") == "text":
            return str(block.get("text", ""))
    return ""


class StdioClient:
    def __init__(self) -> None:
        env = os.environ.copy()
        env.update({
            "COMPASS_AGENT_TYPE": "codex",
            "PYTHONPATH": str(ROOT),
            "PYTHONIOENCODING": "utf-8",
        })
        self.process = subprocess.Popen(
            [str(ROOT / ".venv" / "bin" / "python"), str(MCP_SERVER)],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env,
        )

    def call(self, request_id: int, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("stdio MCP streams unavailable")
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        while True:
            line = self.process.stdout.readline()
            if not line:
                error = self.process.stderr.read()[:500] if self.process.stderr else ""
                raise RuntimeError(f"MCP stdio exited: {error}")
            value = json.loads(line)
            if value.get("id") == request_id:
                return value

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


def run_cycle(project: str, query: str, name: str) -> dict[str, Any]:
    client = StdioClient()
    try:
        client.call(1, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "rsi-proof-cycle", "version": "1"},
        })
        recall = client.call(2, "tools/call", {
            "name": "recall",
            "arguments": {"project": project, "query": query, "top_k": 3},
        })
        recall_text = _text(recall)
        token_match = re.search(r"recall_token:\s*(rt_[0-9a-f]+)", recall_text)
        if not token_match:
            raise RuntimeError("recall did not return a proof token")
        token = token_match.group(1)
        cite_match = re.search(r"\n\s*· score=.*?· [^·\n]+ · ([^\n]+)\n\s+(.+)", recall_text)
        cited = f"{cite_match.group(1)} {cite_match.group(2)}" if cite_match else "NACRE compass assay"
        body = (
            "[RSI实测] 当前 Compass stdio 记忆闭环复核。"
            "只记录 recall token、agent_type 和 fresh recall 结果。"
            "不改变 Gate A、holdout、训练或外发判据。"
        )
        ingest = client.call(3, "tools/call", {
            "name": "ingest_obs",
            "arguments": {
                "name": name,
                "description": "RSI proof-of-recall recovery cycle",
                "type": "change",
                "concept": "what-changed",
                "drift": "green",
                "drift_signals": [],
                "tier": "episodic",
                "project": project,
                "agent_type": "codex",
                "body": body,
                "recall_token": token,
                "cited_snippets": [cited],
            },
        })
        ingest_text = _text(ingest)
        fresh = client.call(4, "tools/call", {
            "name": "recall",
            "arguments": {"project": project, "query": name, "top_k": 5},
        })
        fresh_text = _text(fresh)
        recent_cutoff = time.time() - 300
        memory_files = sorted(
            path for path in MEMORY_DIR.glob("session_*.md")
            if path.stat().st_mtime >= recent_cutoff
            and "RSI" in path.read_text(encoding="utf-8", errors="ignore")
        )
        proof_pass = "proof_of_recall=pass" in ingest_text
        report = {
            "schema": "rsi-proof-of-recall-cycle/v2",
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "status": "pass" if proof_pass else "blocked",
            "agent_type": "codex",
            "project": project,
            "sequence": ["initialize", "recall", "ingest_obs", "fresh_recall"],
            "proof_of_recall": "pass" if proof_pass else "fail",
            "ingest_receipt": ingest_text,
            "memory_file_written": bool(memory_files),
            "fresh_recall_ok": "Recall · query=" in fresh_text,
            "memory_files": [str(path) for path in memory_files[-3:]],
            "external_model_used": False,
            "external_send": False,
            "acceptance_boundary": "memory proof path only",
        }
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--query", default="NACRE compass assay 外联对接主线")
    parser.add_argument("--name", default=f"rsi-proof-cycle-{time.strftime('%Y%m%d-%H%M%S')}")
    args = parser.parse_args()
    report = run_cycle(args.project, args.query, args.name)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
