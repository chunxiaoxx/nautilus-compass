"""A4 · Insert audit_tool_call into 4 tools (propose_code_change / register_dynamic_tool / self_modify / compass_drift_check).

Run on cloud after copying to /tmp/audit_4_tools.py:
  python3 /tmp/audit_4_tools.py

Patches files in /tmp/v5-local-v2/ (worktree only · production untouched).
"""
from __future__ import annotations
import ast
import pathlib
import sys

WT = pathlib.Path("/tmp/v5-local-v2")

PATCHES = []

# ─────────────────────────────────────────────────────────────────────
# Patch 1 · platform_tools_mixin.py · propose_code_change handler
# ─────────────────────────────────────────────────────────────────────
PT = WT / "nautilus_v5/platform_tools_mixin.py"
PT_OLD = '''                pid = getattr(proposal, "proposal_id", str(proposal))'''
PT_NEW = '''                pid = getattr(proposal, "proposal_id", str(proposal))
                # 2026-05-06 A4 · audit propose_code_change
                try:
                    from .learning.tool_audit import audit_tool_call
                    await audit_tool_call(
                        self.platform_admin._pool, self.agent_id,
                        "propose_code_change",
                        f"title={(title or '')[:80]} target={(target_file or '')[:80]} conf={confidence}",
                        f"proposal_id={pid}",
                        True, 0,
                    )
                except Exception:
                    pass'''
PATCHES.append(("propose_code_change audit", PT, PT_OLD, PT_NEW))

# ─────────────────────────────────────────────────────────────────────
# Patch 2 · platform_tools_mixin.py · register_dynamic_tool handler
# Find the register block · insert audit before logger.info("Dynamic tool gen registered")
# ─────────────────────────────────────────────────────────────────────
PT_OLD2 = '''        logger.info("Dynamic tool gen registered · register_dynamic_tool")'''
PT_NEW2 = '''        logger.info("Dynamic tool gen registered · register_dynamic_tool")

        # 2026-05-06 A4 · wrap register_dynamic_tool to audit
        _orig_rdt = register_dynamic_tool
        agent_self_rdt = self
        async def register_dynamic_tool(name: str, description: str, code: str,
                                         params_schema: str = "", emoji: str = "🔧") -> str:
            import time as _t
            _t0 = _t.time()
            _res = await _orig_rdt(name, description, code, params_schema, emoji)
            try:
                from .learning.tool_audit import audit_tool_call
                await audit_tool_call(
                    agent_self_rdt.platform_admin._pool, agent_self_rdt.agent_id,
                    "register_dynamic_tool",
                    f"name={name} desc={description[:60]} code_len={len(code)}",
                    str(_res)[:500],
                    "error" not in str(_res).lower(),
                    int((_t.time() - _t0) * 1000),
                )
            except Exception:
                pass
            return _res
        # 真重 register · 替换 wrapper
        try:
            self.tool_registry.deregister("register_dynamic_tool")
        except Exception:
            pass
        self.tool_registry.register(
            name="register_dynamic_tool", handler=register_dynamic_tool,
            schema={"name": "register_dynamic_tool",
                    "description": "Generate a new tool from Python code (sandboxed). Audited.",
                    "parameters": {"type": "object", "properties": {
                        "name": {"type": "string"}, "description": {"type": "string"},
                        "code": {"type": "string"}, "params_schema": {"type": "string"},
                        "emoji": {"type": "string"}}, "required": ["name", "description", "code"]}},
            description="Audited dynamic tool generator.", emoji="🛠️",
        )'''
PATCHES.append(("register_dynamic_tool audit wrapper", PT, PT_OLD2, PT_NEW2))

# ─────────────────────────────────────────────────────────────────────
# Patch 3 · platform_tools_mixin.py · compass_drift_check handler (already wired earlier)
# Insert audit inside the closure
# ─────────────────────────────────────────────────────────────────────
PT_OLD3 = '''                    if alert is None:
                        return json.dumps({"drift": False, "message": "prompt aligned with anchors · no alert"})
                    return json.dumps({'''
PT_NEW3 = '''                    if alert is None:
                        try:
                            from .learning.tool_audit import audit_tool_call
                            await audit_tool_call(
                                agent_self2.platform_admin._pool, agent_self2.agent_id,
                                "compass_drift_check",
                                f"prompt={prompt[:120]} project={project}",
                                "no_alert",
                                True, 0,
                            )
                        except Exception:
                            pass
                        return json.dumps({"drift": False, "message": "prompt aligned with anchors · no alert"})
                    try:
                        from .learning.tool_audit import audit_tool_call
                        await audit_tool_call(
                            agent_self2.platform_admin._pool, agent_self2.agent_id,
                            "compass_drift_check",
                            f"prompt={prompt[:120]} project={project}",
                            f"drift score={alert.score:.3f}",
                            True, 0,
                        )
                    except Exception:
                        pass
                    return json.dumps({'''
PATCHES.append(("compass_drift_check audit", PT, PT_OLD3, PT_NEW3))

# ─────────────────────────────────────────────────────────────────────
# Patch 4 · platform_tools_mixin.py · self_modify wrapper (already wired earlier)
# Insert audit inside the closure
# ─────────────────────────────────────────────────────────────────────
PT_OLD4 = '''            agent_self = self  # closure ref · platform_admin set 在 awaken 之后
            async def self_modify_fn(filepath: str, content: str, summary: str = "") -> str:
                if agent_self.platform_admin is None:
                    return '{"error": "platform_admin not ready · awaken pending"}'
                _real = make_self_modify_tool(agent_self.agent_id, agent_self.platform_admin._pool)
                return await _real(filepath, content, summary)'''
PT_NEW4 = '''            agent_self = self  # closure ref · platform_admin set 在 awaken 之后
            async def self_modify_fn(filepath: str, content: str, summary: str = "") -> str:
                import time as _t
                _t0 = _t.time()
                if agent_self.platform_admin is None:
                    return '{"error": "platform_admin not ready · awaken pending"}'
                _real = make_self_modify_tool(agent_self.agent_id, agent_self.platform_admin._pool)
                _res = await _real(filepath, content, summary)
                try:
                    from .learning.tool_audit import audit_tool_call
                    _ok = "error" not in (_res or "").lower()
                    await audit_tool_call(
                        agent_self.platform_admin._pool, agent_self.agent_id,
                        "self_modify",
                        f"file={filepath} content_len={len(content)} summary={summary[:80]}",
                        (_res or "")[:500],
                        _ok, int((_t.time() - _t0) * 1000),
                    )
                except Exception:
                    pass
                return _res'''
PATCHES.append(("self_modify audit", PT, PT_OLD4, PT_NEW4))


def main():
    src_cache = {}
    for name, path, old, new in PATCHES:
        if path not in src_cache:
            src_cache[path] = path.read_text()
        src = src_cache[path]
        if old not in src:
            print(f"FAIL · anchor missing · {name} · in {path.name}", file=sys.stderr)
            sys.exit(2)
        src_cache[path] = src.replace(old, new)
        print(f"ok · {name}")

    # Validate AST then write
    for path, src in src_cache.items():
        try:
            ast.parse(src)
        except SyntaxError as e:
            print(f"FAIL · ast parse · {path.name} · {e}", file=sys.stderr)
            sys.exit(3)
        path.write_text(src)
        print(f"wrote · {path.name} · {len(src)} bytes")


if __name__ == "__main__":
    main()
