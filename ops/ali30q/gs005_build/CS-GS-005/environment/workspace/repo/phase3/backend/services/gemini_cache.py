"""
Gemini Content Cache — cache long system prompts to save tokens and reduce latency.
Uses createCachedContent API for frequently used contexts (RAID prompts, platform docs).
"""
import logging
import os
from typing import Optional, Dict

logger = logging.getLogger(__name__)

_cache_store: Dict[str, str] = {}  # key -> cache_name


async def create_or_get_cache(
    key: str,
    content: str,
    model: str = "gemini-2.5-flash",
    ttl_minutes: int = 60,
) -> Optional[str]:
    """Create a cached content resource or return existing cache name."""
    import asyncio

    if key in _cache_store:
        return _cache_store[key]

    def _create():
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

        try:
            cache = client.caches.create(
                model=model,
                config=types.CreateCachedContentConfig(
                    contents=[content],
                    ttl=f"{ttl_minutes * 60}s",
                    display_name=f"nautilus-{key}",
                ),
            )
            return cache.name
        except Exception as e:
            logger.warning("Cache creation failed for %s: %s", key, e)
            return None

    cache_name = await asyncio.to_thread(_create)
    if cache_name:
        _cache_store[key] = cache_name
    return cache_name


async def generate_with_cache(
    cache_name: str,
    prompt: str,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 4096,
) -> str:
    """Generate content using a cached context."""
    import asyncio

    def _gen():
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                cached_content=cache_name,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text or ""

    return await asyncio.to_thread(_gen)
