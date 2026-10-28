"""
Context Compressor — token-aware conversation compression.

Ported from Hermes agent (context_compressor.py), adapted for Nautilus LLM layer.
Keeps head (system+first exchange) and tail (recent context) intact.
Compresses middle into structured LLM summary.
"""

import logging

logger = logging.getLogger(__name__)


class ContextCompressor:
    def __init__(self, llm, threshold_tokens=100000, protect_tail_tokens=20000):
        self.llm = llm  # Nautilus LLM instance (has .chat() method)
        self.threshold_tokens = threshold_tokens
        self.protect_tail_tokens = protect_tail_tokens
        self._previous_summary = ""

    def estimate_tokens(self, messages: list) -> int:
        """Rough token estimate: 4 chars ~ 1 token."""
        return sum(len(str(m.get("content", ""))) // 4 for m in messages)

    def should_compress(self, messages: list) -> bool:
        return self.estimate_tokens(messages) > self.threshold_tokens

    def compress(self, messages: list) -> list:
        """Compress conversation, preserving head and tail."""
        if not self.should_compress(messages):
            return messages

        total_tokens = self.estimate_tokens(messages)

        # Find head boundary (protect first 3 exchanges = ~6 messages)
        head_end = min(6, len(messages))

        # Find tail boundary (protect last N tokens worth of messages)
        tail_start = len(messages)
        tail_tokens = 0
        while tail_start > head_end and tail_tokens < self.protect_tail_tokens:
            tail_start -= 1
            tail_tokens += len(str(messages[tail_start].get("content", ""))) // 4

        # Middle section to compress
        middle = messages[head_end:tail_start]
        if not middle:
            return messages

        # Generate structured summary
        summary = self._summarize(middle)
        self._previous_summary = summary

        # Reconstruct: head + summary message + tail
        summary_msg = {
            "role": "user",
            "content": f"[CONTEXT SUMMARY — {len(middle)} messages compressed]\n{summary}",
        }

        compressed = messages[:head_end] + [summary_msg] + messages[tail_start:]
        old_tokens = total_tokens
        new_tokens = self.estimate_tokens(compressed)
        logger.info(
            "context compressed: %d messages -> summary + %d tail, tokens %d -> %d (%.0f%% reduction)",
            len(middle),
            len(messages) - tail_start,
            old_tokens,
            new_tokens,
            (1 - new_tokens / max(old_tokens, 1)) * 100,
        )
        return compressed

    def _summarize(self, messages: list) -> str:
        """Use LLM to create structured summary of compressed messages."""
        # Build content for summarization
        content_parts = []
        for m in messages:
            role = m.get("role", "?")
            text = str(m.get("content", ""))[:500]  # Truncate long messages
            content_parts.append(f"[{role}] {text}")

        conversation_text = "\n".join(content_parts)[:15000]  # Cap input

        previous = (
            f"\nPrevious summary:\n{self._previous_summary}"
            if self._previous_summary
            else ""
        )

        prompt = f"""Summarize this conversation segment into a structured context note.
{previous}

Conversation ({len(messages)} messages):
{conversation_text}

Format:
## Goal
What is the agent trying to accomplish?

## Progress
- Done: [completed items]
- In Progress: [current work]
- Blocked: [issues]

## Key Decisions
[important choices made]

## Relevant Files
[files mentioned or modified]

## Critical Context
[anything the agent MUST remember]

Be concise. Max 500 words."""

        try:
            summary = self.llm.chat(
                prompt=prompt,
                system="You are a context summarizer. Extract essential information only. Be concise.",
                max_tokens=2000,
                temperature=0.2,
            )
            return summary.strip()
        except Exception as e:
            # Fallback: simple concatenation of key messages
            logger.warning("LLM summary failed, using keyword fallback: %s", e)
            key_msgs = [
                m
                for m in messages
                if any(
                    k in str(m.get("content", "")).lower()
                    for k in ["error", "fix", "done", "created", "important"]
                )
            ]
            if key_msgs:
                return "Key messages:\n" + "\n".join(
                    f"- {str(m.get('content', ''))[:200]}" for m in key_msgs[:10]
                )
            return f"({len(messages)} messages compressed, LLM summary unavailable: {e})"
