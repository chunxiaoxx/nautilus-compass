# /compass-recall — Semantic Recall on Project Memory

Run a one-shot semantic recall against the active project's `memory/` entries: top hits with relevance scores, anchor drift annotations, and links.

## When to use

- "Have we discussed this before?" — search past memory
- Pre-flight check before designing — surface prior decisions
- Confirm whether a recall hit exists before relying on it implicitly

## How to run

Invoke `recall.py` with `--query` (and `--bge` to force daemon mode, or omit `--bge` to let the script auto-promote when the BGE daemon at `127.0.0.1:9876` is alive):

```bash
python ~/.claude/plugins/nautilus-compass/recall.py --bge --query "$ARGUMENTS"
```

If the BGE daemon is **not** running, the script falls back to metadata-only mode (no embedding similarity, just keyword/anchor scoring). Tell the user when this happens — the hits will be lower quality.

## Daemon health

Quick liveness check (used internally by the plugin):

```bash
echo '{"action":"ping"}' | nc -w 2 127.0.0.1 9876
```

A `{"pong": true, ...}` response means BGE-m3 is loaded and ready.

If absent, start it:

```bash
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
```

## What to report back

- Headline: `N hits in <memory dir>` (or `no hits` / `daemon down — metadata mode`)
- For each hit: score, file name, one-line snippet, drift anchor flag (if any)
- Strategy hits (from the strategy_store) take precedence — surface them first

⚠️ **Time-stamp discipline** — memory older than 7 days may reflect outdated user intent. The CLI emits a banner reminder; preserve it when forwarding to the user.
