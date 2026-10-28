"""
LLM Client - Unified interface for MiniMax M3 via Anthropic SDK.
"""
import os
import logging
from typing import Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Singleton client
_client: Optional["LLMClient"] = None


class LLMClient:
    """Wrapper around Anthropic SDK configured for MiniMax M3."""

    DEFAULT_MODEL = "MiniMax-M3"
    DEFAULT_BASE_URL = "https://api.minimaxi.com/anthropic"
    # Per-request timeout (seconds). A hung request must raise so callers like
    # _chat_safe retry/degrade, instead of deadlocking a ThreadPoolExecutor.map
    # (the Phase-3 seed3 hang root cause).
    DEFAULT_TIMEOUT = 180.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # 通道优先级(9/16 定,对齐 digest 三层纪律:自有中转站优先):
        # ① CHUNXIAO_API_KEY+CHUNXIAO_BASE_URL(自有站,模型 CHUNXIAO_MODEL)
        # ② MINIMAX_API_KEY(minimaxi anthropic 直连,9/16 实测已 401,留后备)
        # ③ ANTHROPIC_API_KEY。显式参数最优先(测试用)。
        # 自有站 base_url 若带 /v1 尾巴须剥除(Anthropic SDK 自拼 /v1/messages,
        # 否则 404 /v1/v1/messages——9/16 实测)。
        if os.getenv("CHUNXIAO_API_KEY") and os.getenv("CHUNXIAO_BASE_URL"):
            resolved_key = api_key or os.getenv("CHUNXIAO_API_KEY")
            _url = os.getenv("CHUNXIAO_BASE_URL").rstrip("/")
            if _url.endswith("/v1"):
                _url = _url[:-3]
            resolved_url = base_url or _url
            self.model = (model or os.getenv("CHUNXIAO_MODEL")
                          or os.getenv("LLM_MODEL") or self.DEFAULT_MODEL)
        else:
            resolved_key = api_key or os.getenv("MINIMAX_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
            # Prioritize MINIMAX_BASE_URL; ignore ANTHROPIC_BASE_URL (may point to anthropic.com)
            resolved_url = os.getenv("MINIMAX_BASE_URL") or base_url or self.DEFAULT_BASE_URL
            self.model = model or os.getenv("LLM_MODEL", self.DEFAULT_MODEL)

        if not resolved_key:
            raise ValueError(
                "No API key found. Set CHUNXIAO_API_KEY/CHUNXIAO_BASE_URL"
                " or MINIMAX_API_KEY or ANTHROPIC_API_KEY env var."
            )

        self.client = Anthropic(api_key=resolved_key, base_url=resolved_url)
        logger.info(f"LLMClient initialized: model={self.model}, base_url={resolved_url}")

    def chat(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 32768,
        temperature: float = 0.3,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> str:
        """
        Send a single message and get a text response.

        max_tokens default raised 4096→32768 (2026-09-10): thinking-mode
        responses spend the budget on reasoning blocks first; at 4096 the
        answer never got generated and only a ThinkingBlock came back.

        Args:
            prompt: User message
            system: System prompt
            max_tokens: Max output tokens
            temperature: Sampling temperature
            timeout: Per-request timeout in seconds (raises on a hung request)

        Returns:
            Model's text response
        """
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "timeout": timeout,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        try:
            return _extract_text(response)
        except ValueError:
            # 2026-09-15: thinking-only observed at 32k on structural-generation
            # goals (soul fw-tpl, MiniMax-M3 via relay) — reasoning is unbounded
            # in tendency. One adaptive retry at 2x budget, fail loud after.
            kwargs["max_tokens"] = max_tokens * 2
            response = self.client.messages.create(**kwargs)
            return _extract_text(response)

    def chat_with_messages(
        self,
        messages: list,
        system: str = "",
        max_tokens: int = 32768,
        temperature: float = 0.3,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> str:
        """
        Multi-turn conversation.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            system: System prompt
            max_tokens: Max output tokens
            temperature: Sampling temperature
            timeout: Per-request timeout in seconds (raises on a hung request)

        Returns:
            Model's text response
        """
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "timeout": timeout,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return _extract_text(response)


def _extract_text(response) -> str:
    """Extract text from response, skipping ThinkingBlocks."""
    for block in response.content:
        block_type = getattr(block, "type", None)
        # Skip thinking blocks explicitly
        if block_type == "thinking":
            continue
        if block_type == "text" and hasattr(block, "text"):
            return block.text
    # Second pass: any block with text attribute that isn't a ThinkingBlock
    for block in response.content:
        if hasattr(block, "text") and not hasattr(block, "thinking") and not hasattr(block, "signature"):
            return block.text
    # 2026-09-10: a thinking-only response means the budget was exhausted by
    # reasoning before the answer was written (observed at max_tokens=4096).
    # The old str(last) fallback returned 18k chars of thinking as the
    # "answer", which downstream file-block parsing silently parsed as zero
    # files. Raising lets ship()'s retry loop take another attempt.
    if response.content:
        last = response.content[-1]
        if hasattr(last, "text"):
            return last.text
        raise ValueError(
            "response contained only non-text blocks (thinking-only — likely "
            "max_tokens exhausted by reasoning); retry with a higher budget"
        )
    raise ValueError("No text content in response")


def get_llm_client() -> LLMClient:
    """Get or create singleton LLM client."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
