# Gemini query-rewrite · opt-in recall enhancement (2026-06-05)

## Goal
Optionally rewrite a recall query before retrieval (expand abbreviations, add
synonyms) to lift recall on terse/ambiguous queries. Opt-in, default off →
black-box-local hot path preserved (no LLM unless explicitly enabled).

## Build on existing infra (not reinvent · anchor #5)
- `judges/gemini_flash.py` `GeminiFlashJudge.generate(prompt) -> str|None` —
  complete lazy opt-in Gemini 2.5 Flash provider (Vertex SA, returns None on any
  failure). Reused for the rewrite call.
- `llm_opt_in.py` — flag registry (`OptInFlag`, `is_enabled(flag)` per-call).
  Add a `query_rewrite` flag.

## Architecture
New module `query_rewrite.py` isolates ALL LLM contact:
```
rewrite_query(query: str) -> str
  · flag off                → return query unchanged (byte-identical default)
  · flag on, gemini ok      → return rewritten query
  · flag on, gemini None/err → return ORIGINAL query (recall never degraded/broken)
```
- Flag: `query_rewrite` in `llm_opt_in.py`, env `COMPASS_PROD_QUERY_REWRITE`.
  Effective only when the gemini provider is also enabled
  (`COMPASS_USE_GEMINI_FLASH`); if the provider is off, `rewrite_query` is a
  no-op (defense: never silently require an LLM the user didn't enable).
- Prompt (low temperature, short): "Rewrite this memory-search query to maximize
  retrieval recall: expand abbreviations, add 2-3 synonyms, keep it one line.
  Return ONLY the rewritten query, no preamble." Cap output length; strip.
- Guardrails: if the model returns empty / too-long / suspicious output, fall
  back to the original query.

### Hook (user-approved: daemon recall)
`daemon.handle_request`, right after `query` is extracted and validated, behind
the flag:
```
if _PROD_QUERY_REWRITE_USE:
    query = query_rewrite.rewrite_query(query)
```
The embedding + scoring then use the (possibly rewritten) query. The P9 recall
cache already keys on the query string, so rewrites cache naturally. The LLM call
lives ONLY in `query_rewrite.py` — daemon core stays LLM-free by default.

## Safety / constraints
- Default off → daemon behavior byte-identical, zero LLM (honors
  gemini_flash.py's "NEVER call from default recall").
- Any gemini failure → original query (recall robustness invariant).
- Latency: +1 gemini call (~hundreds ms) only when opted in.
- Black-box: the LLM never touches embeddings or stored memory — only the
  transient query string is rewritten.

## Testing
TDD with a MOCKED gemini provider (no live API):
- flag off → identity.
- flag on + provider off → identity (no-op).
- flag on + mock returns rewrite → rewritten used.
- flag on + mock returns None/empty/over-long → original (fallback).
- daemon integration: monkeypatch rewrite + assert the scored query is the
  rewritten one when flag on; identical path when off.
Live gemini verification (real Vertex creds + `COMPASS_USE_GEMINI_FLASH=1`) is a
manual gated smoke, deferred.

## Out of scope (YAGNI)
- No rewrite for drift/ingest (recall only).
- No multi-candidate / HyDE expansion (single rewrite).
- No local-LLM rewrite path (Qwen) in this iteration — gemini only, opt-in.
