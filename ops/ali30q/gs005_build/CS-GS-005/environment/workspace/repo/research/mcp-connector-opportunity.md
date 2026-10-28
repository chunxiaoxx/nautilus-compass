# MCP Nautilus Connector — Ecosystem Opportunity

## Summary
Model Context Protocol (MCP) is an emerging open standard (Anthropic, November 2024) for AI-tool integration. Adopted by OpenAI, Google DeepMind. Creates N×M connector ecosystem.

## Why This Matters for Nautilus
- MCP solves the "N×M problem" — each data source needs only ONE connector, not N connectors per AI provider
- Nautilus agents could expose capabilities as MCP tools
- Any MCP-compatible client (Claude, GPT, Gemini) could then interact with Nautilus

## bounty Created
- Title: MCP Nautilus Connector
- Reward: 100 NAU
- Task: Build reference MCP server exposing Nautilus agent capabilities as MCP tools

## Technical Notes
- Transport: stdio (local) or SSE (remote)
- Protocol: JSON-RPC 2.0
- SDKs: Python, TypeScript, C#, Java available
- MCP is NOT replacing LangChain/LangGraph — it's a complementary connectivity layer

## Reference
- MCP GitHub: github.com/modelcontextprotocol
- SDK: Python, TypeScript, C#, Java
