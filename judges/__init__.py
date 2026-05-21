"""nautilus_compass.judges · v2.0+ · external LLM judges for benchmark / paper ONLY.

CRITICAL CONSTRAINT (per user 2026-04-28 rule + daemon.py:12-13 verbatim):
  "永远只 BGE local · 不读 GEMINI_API_KEY · 完全本地"

This subpackage is OPT-IN only · activated by explicit env var
COMPASS_USE_GEMINI_FLASH=1 (or analogous flags). Used for:
  - LongMemEval-S benchmark judge ($0 with service account)
  - paper3 cross-LLM ablation (Flash + DeepSeek + MiniMax)
  - NOT for ingest path · NOT for default recall · NOT for production users

Default behavior: judges remain DISABLED unless env explicitly opts in.
"""
