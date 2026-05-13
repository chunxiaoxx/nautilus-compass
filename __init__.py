"""nautilus_compass · cross-agent memory layer for the Nautilus platform.

Provides:
  · BGE-m3 dense recall + bge-reranker-v2-m3 cross-encoder reranking
  · MCP server (Claude Desktop / Cline / Cursor compatible)
  · A2A protocol adapter for cross-agent message routing
  · Drift detector (anchor-based · AUC=0.92)
  · Session writer / search / drift-history utilities

Submodules are exposed lazily; import only what you need to keep startup fast.
"""

__version__ = "1.5.1"
