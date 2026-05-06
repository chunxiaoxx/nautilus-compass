"""compass · Cross-client memory federation demo.

演示 compass 的核心独占能力 — 同一 user_id 跨多 MCP client 共享 memory.
不需要任何额外服务 · compass.nautilus.social platform 直接接.

场景:
  1. Claude Desktop (or compass-mcp 直接调) 写 obs A: "user prefers 简洁回复"
  2. Cursor (or compass-mcp via cursor extension) 写 obs B: "user 在做 ZenMind"
  3. Hermes (via SDK) 写 obs C: "user wallet=0x...· stake=1000"
  4. 任何 client 调 recall("user 偏好") → 看到 A
  5. 任何 client 调 recall("ZenMind") → 看到 B
  6. 任何 client 调 drift_history → 看到全部 ABC 的 drift timeline

跑法:
  python examples/multi_client_demo.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))

from compass_client import CompassClient


SHARED_USER_ID = "u_demo_chunx_2026"
BASE_URL = "https://compass.nautilus.social"   # 或 http://localhost:8765 本地


def write_from_claude_desktop():
    """Pretend we're Claude Desktop · write 1 obs."""
    client = CompassClient(
        user_id=SHARED_USER_ID,
        agent_id="ag_claude_desktop_main",
        agent_type="claude-code",
        base_url=BASE_URL,
    )
    return client.ingest_obs(
        name="user 偏好简洁回复",
        description="用户多次表达不喜欢冗长解释 · 喜欢直接给答案",
        body="证据: 5/5 在 Claude Desktop 多次说 'too verbose, just answer'",
        type_="discovery",
        concept="pattern",
        drift="green",
    )


def write_from_cursor():
    """Pretend we're Cursor · write 1 obs."""
    client = CompassClient(
        user_id=SHARED_USER_ID,
        agent_id="ag_cursor_main",
        agent_type="cursor",
        base_url=BASE_URL,
    )
    return client.ingest_obs(
        name="user 在做 ZenMind 项目",
        description="用户主要在 ZenMind 仓库工作 · 跟禅修 + AI 相关",
        body="技术栈: TypeScript · React · trpc · Drizzle",
        type_="discovery",
        concept="why-it-exists",
        drift="green",
    )


def write_from_hermes():
    """Pretend we're Hermes (server-side agent) · write 1 obs with red drift."""
    client = CompassClient(
        user_id=SHARED_USER_ID,
        agent_id="ag_hermes_loop_main",
        agent_type="hermes",
        base_url=BASE_URL,
    )
    return client.ingest_obs(
        name="hermes 重复无效尝试",
        description="hermes 第 3 次重派同一个 issue · 没改方法",
        body="issue=hi-2331 · 5/3 5/4 5/5 都派发 · 都 timeout",
        type_="bugfix",
        concept="gotcha",
        drift="red",
        drift_signals=["3 次重派同一 issue", "未分析失败原因"],
    )


def recall_from_any_client(query: str, agent_type: str = "claude-code"):
    """Cross-agent recall · 不限单 agent_type."""
    client = CompassClient(
        user_id=SHARED_USER_ID,
        agent_id=f"ag_{agent_type}_recall_demo",
        agent_type=agent_type,
        base_url=BASE_URL,
    )
    return client.recall(query=query, top_k=5, cross_agent=True)


def query_drift_history(client_label: str = "claude-code"):
    """Pretend we're some client asking for drift timeline."""
    client = CompassClient(
        user_id=SHARED_USER_ID,
        agent_id=f"ag_{client_label}_drift",
        agent_type=client_label,
        base_url=BASE_URL,
    )
    # drift_history 通过 MCP tool 走 · 这里走 HTTP /v1/recall + drift filter
    return client.recall(query="*", top_k=10, cross_agent=True, drift="red")


def query_user_profile():
    client = CompassClient(
        user_id=SHARED_USER_ID,
        agent_id="ag_profile_query",
        agent_type="claude-code",
        base_url=BASE_URL,
    )
    return client.profile()


def demo():
    print("=" * 60)
    print(f"compass cross-client federation demo · user={SHARED_USER_ID}")
    print("=" * 60)
    print(f"target: {BASE_URL}")
    print("(this demo expects /v1/observations endpoint to exist · v0.9.0+)")
    print()

    print("[1] Claude Desktop writes obs A: 'user 偏好简洁回复'")
    r1 = write_from_claude_desktop()
    print(f"    → {json.dumps(r1, ensure_ascii=False)[:200]}")
    print()

    print("[2] Cursor writes obs B: 'user 在做 ZenMind'")
    r2 = write_from_cursor()
    print(f"    → {json.dumps(r2, ensure_ascii=False)[:200]}")
    print()

    print("[3] Hermes writes obs C with drift=red: 'hermes 重复无效尝试'")
    r3 = write_from_hermes()
    print(f"    → {json.dumps(r3, ensure_ascii=False)[:200]}")
    print()

    time.sleep(1)  # 让 server 索引

    print("[4] Recall 'user 偏好' from Claude Desktop perspective:")
    r4 = recall_from_any_client("user 偏好")
    print(f"    → {json.dumps(r4, ensure_ascii=False)[:300]}")
    print()

    print("[5] Recall 'ZenMind' from Cursor perspective:")
    r5 = recall_from_any_client("ZenMind", agent_type="cursor")
    print(f"    → {json.dumps(r5, ensure_ascii=False)[:300]}")
    print()

    print("[6] drift=red history (showing the hermes obs from any client):")
    r6 = query_drift_history()
    print(f"    → {json.dumps(r6, ensure_ascii=False)[:300]}")
    print()

    print("[7] user profile aggregate:")
    r7 = query_user_profile()
    print(f"    → {json.dumps(r7, ensure_ascii=False)[:400]}")
    print()

    print("=" * 60)
    print("Federation works iff:")
    print("  - All 3 writes succeed (or buffer if /v1/observations not deployed yet)")
    print("  - Recalls return cross-agent results (not just one agent)")
    print("  - drift_history shows hermes obs (red) from any querying client")
    print("=" * 60)


if __name__ == "__main__":
    demo()
