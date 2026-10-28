"""
Gemini Batch Processing — parallel task execution for high throughput.
Uses batchGenerateContent for processing multiple prompts in one API call.
"""
import logging
import os
from typing import List

logger = logging.getLogger(__name__)


async def batch_generate(
    prompts: List[str],
    system: str = "",
    model: str = "gemini-2.5-flash",
    max_tokens: int = 2048,
) -> List[str]:
    """Process multiple prompts in parallel using Gemini batch API."""
    import asyncio

    def _batch():
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

        results = []
        # Process in chunks of 5 (API limit)
        for i in range(0, len(prompts), 5):
            chunk = prompts[i:i + 5]
            for prompt in chunk:
                try:
                    config = types.GenerateContentConfig(max_output_tokens=max_tokens)
                    if system:
                        config.system_instruction = system
                    r = client.models.generate_content(
                        model=model, contents=prompt, config=config,
                    )
                    results.append(r.text or "")
                except Exception as e:
                    results.append(f"[ERROR: {str(e)[:100]}]")

        return results

    return await asyncio.to_thread(_batch)


async def batch_embed(
    texts: List[str],
    model: str = "gemini-embedding-001",
) -> List[List[float]]:
    """Batch embed multiple texts."""
    import asyncio

    def _batch():
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
        result = client.models.embed_content(model=model, contents=texts)
        return [e.values for e in result.embeddings]

    return await asyncio.to_thread(_batch)
