"""A4 补 · instrument ask_kairos / review_by_kairos / send_to_agent.

Patch /tmp/v5-local-v2/nautilus_v5/platform_tools_mixin.py · 3 closure handlers.
"""
from __future__ import annotations
import ast
import pathlib
import sys

PT = pathlib.Path("/tmp/v5-local-v2/nautilus_v5/platform_tools_mixin.py")

PATCHES = []

# ─────────────────────────────────────────
# 1 · send_to_agent · audit on success
# ─────────────────────────────────────────
OLD1 = '''        async def send_to_agent(agent_id: str, content: str, msg_type: str = "request") -> str:
            try:
                mtype = A2AMessageType(msg_type.lower())
            except ValueError:
                mtype = A2AMessageType.REQUEST'''

NEW1 = '''        async def send_to_agent(agent_id: str, content: str, msg_type: str = "request") -> str:
            import time as _t_sa
            _t0_sa = _t_sa.time()
            try:
                mtype = A2AMessageType(msg_type.lower())
            except ValueError:
                mtype = A2AMessageType.REQUEST'''
PATCHES.append(("send_to_agent timer start", OLD1, NEW1))

OLD2 = '''            mid = await self.platform_admin.send_a2a_message(
                from_agent=self.agent_id, to_agent=agent_id,
                content=content[:3000], msg_type=msg_type,
            )
            return json.dumps({"success": bool(mid), "message_id": mid, "to": agent_id},
                              ensure_ascii=False)'''

NEW2 = '''            mid = await self.platform_admin.send_a2a_message(
                from_agent=self.agent_id, to_agent=agent_id,
                content=content[:3000], msg_type=msg_type,
            )
            try:
                from .learning.tool_audit import audit_tool_call
                await audit_tool_call(
                    self.platform_admin._pool, self.agent_id,
                    "send_to_agent",
                    f"to={agent_id} type={msg_type} content={content[:80]}",
                    f"mid={mid}",
                    bool(mid), int((_t_sa.time() - _t0_sa) * 1000),
                )
            except Exception:
                pass
            return json.dumps({"success": bool(mid), "message_id": mid, "to": agent_id},
                              ensure_ascii=False)'''
PATCHES.append(("send_to_agent audit", OLD2, NEW2))

# ─────────────────────────────────────────
# 2 · ask_kairos · audit on return
# ─────────────────────────────────────────
OLD3 = '''        async def ask_kairos(question: str, timeout_s: int = 120) -> str:
            """同步问 Kairos · 发 sync_request · 轮询 inbox 等 response.

            对称 Kairos 的 ask_v5. V5 遇到需深度反思/审查时主动调.
            Kairos 每 cycle ~60s 读 inbox · 120s = 2 cycle 足够.
            """
            import asyncio as _aio
            import time as _time
            mid = await self.platform_admin.send_a2a_message(
                from_agent=self.agent_id, to_agent="kairos",
                content=question[:3000], msg_type="sync_request",
            )'''

NEW3 = '''        async def ask_kairos(question: str, timeout_s: int = 120) -> str:
            """同步问 Kairos · 发 sync_request · 轮询 inbox 等 response.

            对称 Kairos 的 ask_v5. V5 遇到需深度反思/审查时主动调.
            Kairos 每 cycle ~60s 读 inbox · 120s = 2 cycle 足够.
            """
            import asyncio as _aio
            import time as _time
            _t0_ak = _time.time()
            mid = await self.platform_admin.send_a2a_message(
                from_agent=self.agent_id, to_agent="kairos",
                content=question[:3000], msg_type="sync_request",
            )
            # 立即 audit · 即使 kairos 不回 · 真证 V5 真发了 sync_request
            try:
                from .learning.tool_audit import audit_tool_call
                await audit_tool_call(
                    self.platform_admin._pool, self.agent_id,
                    "ask_kairos",
                    f"q={question[:120]} timeout={timeout_s}",
                    f"sync_request mid={mid}",
                    bool(mid), int((_time.time() - _t0_ak) * 1000),
                )
            except Exception:
                pass'''
PATCHES.append(("ask_kairos audit", OLD3, NEW3))

# ─────────────────────────────────────────
# 3 · review_by_kairos · audit on return
# ─────────────────────────────────────────
OLD4 = '''        async def review_by_kairos(content: str, question: str = "", timeout_s: int = 150) -> str:'''

NEW4 = '''        async def review_by_kairos(content: str, question: str = "", timeout_s: int = 150) -> str:
            import time as _time_rk
            _t0_rk = _time_rk.time()'''
PATCHES.append(("review_by_kairos timer start", OLD4, NEW4))

# 接 review_by_kairos return · 找它的 send_a2a_message 调用
OLD5 = '''            mid = await self.platform_admin.send_a2a_message(
                from_agent=self.agent_id, to_agent="kairos",
                content=req[:3000], msg_type="review_request",
            )'''

NEW5 = '''            mid = await self.platform_admin.send_a2a_message(
                from_agent=self.agent_id, to_agent="kairos",
                content=req[:3000], msg_type="review_request",
            )
            try:
                from .learning.tool_audit import audit_tool_call
                await audit_tool_call(
                    self.platform_admin._pool, self.agent_id,
                    "review_by_kairos",
                    f"content_len={len(content)} q={question[:80]}",
                    f"review mid={mid}",
                    bool(mid), int((_time_rk.time() - _t0_rk) * 1000),
                )
            except Exception:
                pass'''
PATCHES.append(("review_by_kairos audit", OLD5, NEW5))


def main():
    src = PT.read_text()
    for name, old, new in PATCHES:
        if old not in src:
            print(f"FAIL · anchor missing · {name}", file=sys.stderr)
            sys.exit(2)
        src = src.replace(old, new)
        print(f"ok · {name}")
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"FAIL · ast: {e}", file=sys.stderr)
        sys.exit(3)
    PT.write_text(src)
    print(f"wrote · platform_tools_mixin.py · {len(src)} bytes")


if __name__ == "__main__":
    main()
