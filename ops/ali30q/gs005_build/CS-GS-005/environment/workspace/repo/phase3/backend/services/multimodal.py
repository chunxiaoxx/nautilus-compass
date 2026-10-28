"""
Multi-modal integration layer for Nautilus.

Handles images, documents, and audio from customers before they reach
AgentBrain.  The actual LLM provider (e.g. Google Gemini) is plugged in
via the LLMProvider interface — swap implementations without touching
business logic.

Flow:
  User message → MessageProcessor.process()
      → detect content type
      → if non-text, delegate to ContentExtractor via LLMProvider
      → return enriched plain-text message for AgentBrain
"""
from __future__ import annotations

import base64
import csv
import io
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Content types
# ---------------------------------------------------------------------------

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE_BASE64 = "image_base64"
    IMAGE_URL = "image_url"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    AUDIO = "audio"


@dataclass(frozen=True)
class DetectedContent:
    """A single piece of detected content inside a user message."""
    content_type: ContentType
    raw_data: str                         # text, base64, or URL
    mime_type: Optional[str] = None       # e.g. image/png, audio/wav
    filename: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessedMessage:
    """Result of running a message through MessageProcessor."""
    original_text: str
    enriched_text: str                    # text with extracted info appended
    detected_types: List[ContentType] = field(default_factory=list)
    extractions: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# LLM provider interface (pluggable)
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    """Abstract base for multi-modal LLM calls."""

    @abstractmethod
    async def process(
        self,
        content_type: ContentType,
        data: str,
        prompt: str,
        *,
        mime_type: Optional[str] = None,
    ) -> str:
        """Send *data* of the given type to the LLM and return extracted text."""


class FallbackProvider(LLMProvider):
    """Returns a polite 'unsupported' message — always available."""

    async def process(
        self,
        content_type: ContentType,
        data: str,
        prompt: str,
        *,
        mime_type: Optional[str] = None,
    ) -> str:
        return (
            f"[Unsupported content type: {content_type.value}. "
            "Please send as plain text or try again later.]"
        )


class GoogleProvider(LLMProvider):
    """
    Google Gemini multimodal provider via Vertex AI.

    Handles: images, audio, video, PDF (as image pages), CSV.
    Requires GOOGLE_APPLICATION_CREDENTIALS env var pointing to SA key JSON.
    """

    def __init__(self, model: str = "gemini-2.0-flash-001"):
        self._model = model

    async def process(
        self,
        content_type: ContentType,
        data: str,
        prompt: str,
        *,
        mime_type: Optional[str] = None,
    ) -> str:
        try:
            from services.google_ai import get_gemini
            gemini = get_gemini(model=self._model)

            if content_type in (ContentType.IMAGE_BASE64, ContentType.IMAGE_URL):
                if content_type == ContentType.IMAGE_URL:
                    # Download the image first
                    import httpx
                    async with httpx.AsyncClient(timeout=15) as client:
                        resp = await client.get(data)
                        img_bytes = resp.content
                    mt = mime_type or "image/jpeg"
                else:
                    img_bytes = base64.b64decode(data)
                    mt = mime_type or "image/png"
                return await gemini.analyze_image(img_bytes, prompt, mime_type=mt)

            elif content_type == ContentType.AUDIO:
                audio_bytes = base64.b64decode(data) if not data.startswith("http") else None
                if audio_bytes:
                    return await gemini.transcribe_audio(
                        audio_bytes, prompt, mime_type=mime_type or "audio/wav"
                    )
                return "[Audio processing requires raw audio data, not URL]"

            elif content_type == ContentType.PDF:
                # Treat PDF as document for text extraction prompt
                return await gemini.chat(
                    f"{prompt}\n\nDocument content (base64 PDF):\n{data[:1000]}..."
                )

            elif content_type == ContentType.CSV:
                return await gemini.chat(f"{prompt}\n\nCSV data:\n{data[:2000]}")

            elif content_type == ContentType.EXCEL:
                return await gemini.chat(f"{prompt}\n\nSpreadsheet data (base64):\n{data[:500]}...")

        except Exception as exc:
            logger.warning("GoogleProvider failed: %s — falling back", exc)

        return await FallbackProvider().process(content_type, data, prompt)


class AnthropicProvider(LLMProvider):
    """Uses Claude vision for images — other types fall back."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-6"):
        self._api_key = api_key
        self._model = model

    async def process(
        self,
        content_type: ContentType,
        data: str,
        prompt: str,
        *,
        mime_type: Optional[str] = None,
    ) -> str:
        if not self._api_key:
            return await FallbackProvider().process(content_type, data, prompt)

        if content_type not in (ContentType.IMAGE_BASE64, ContentType.IMAGE_URL):
            return await FallbackProvider().process(content_type, data, prompt)

        import anthropic  # lazy — only needed when actually called

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        image_block: Dict[str, Any]
        if content_type == ContentType.IMAGE_BASE64:
            image_block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type or "image/png",
                    "data": data,
                },
            }
        else:
            image_block = {
                "type": "image",
                "source": {"type": "url", "url": data},
            }

        resp = await client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": [image_block, {"type": "text", "text": prompt}]},
            ],
        )
        return resp.content[0].text


# ---------------------------------------------------------------------------
# Content detection helpers
# ---------------------------------------------------------------------------

_BASE64_RE = re.compile(
    r"^data:(image/[a-z+]+);base64,([A-Za-z0-9+/=\s]+)$", re.DOTALL
)
_URL_IMAGE_RE = re.compile(
    r"https?://\S+\.(?:png|jpe?g|gif|webp|bmp|svg)(?:\?\S*)?", re.IGNORECASE
)


def _detect_content(text: str, attachments: List[Dict[str, Any]]) -> List[DetectedContent]:
    """Return a list of non-text content items found in *text* or *attachments*."""
    found: List[DetectedContent] = []

    # inline base64 images
    for m in _BASE64_RE.finditer(text):
        found.append(DetectedContent(
            content_type=ContentType.IMAGE_BASE64,
            raw_data=m.group(2),
            mime_type=m.group(1),
        ))

    # inline image URLs
    for m in _URL_IMAGE_RE.finditer(text):
        found.append(DetectedContent(
            content_type=ContentType.IMAGE_URL,
            raw_data=m.group(0),
        ))

    # structured attachments (from API / WeChat bot)
    for att in attachments:
        ct = att.get("content_type", att.get("type", ""))
        data = att.get("data", att.get("url", ""))
        fname = att.get("filename", "")

        if ct.startswith("image/") or ct == "image":
            is_b64 = not data.startswith("http")
            found.append(DetectedContent(
                content_type=ContentType.IMAGE_BASE64 if is_b64 else ContentType.IMAGE_URL,
                raw_data=data,
                mime_type=ct if "/" in ct else None,
                filename=fname,
            ))
        elif ct == "application/pdf" or fname.lower().endswith(".pdf"):
            found.append(DetectedContent(ContentType.PDF, data, ct, fname))
        elif ct in ("text/csv",) or fname.lower().endswith(".csv"):
            found.append(DetectedContent(ContentType.CSV, data, ct, fname))
        elif "spreadsheet" in ct or fname.lower().endswith((".xlsx", ".xls")):
            found.append(DetectedContent(ContentType.EXCEL, data, ct, fname))
        elif ct.startswith("audio/"):
            found.append(DetectedContent(ContentType.AUDIO, data, ct, fname))

    return found


# ---------------------------------------------------------------------------
# ContentExtractor — structured data from unstructured input
# ---------------------------------------------------------------------------

class ContentExtractor:
    """Extracts structured text from non-text content via an LLMProvider."""

    _PROMPTS = {
        ContentType.IMAGE_BASE64: (
            "Describe this image. If it contains a data table, convert it to CSV. "
            "If it contains text, transcribe it."
        ),
        ContentType.IMAGE_URL: (
            "Describe this image. If it contains a data table, convert it to CSV. "
            "If it contains text, transcribe it."
        ),
        ContentType.PDF: "Extract the main content of this PDF as structured text.",
        ContentType.EXCEL: "List column headers and a preview of the first 5 rows.",
        ContentType.CSV: "Summarise this CSV: column headers and row count.",
        ContentType.AUDIO: "Transcribe this audio to text.",
    }

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def extract(self, item: DetectedContent) -> str:
        prompt = self._PROMPTS.get(item.content_type, "Extract useful text.")

        # CSV can be handled locally without an LLM call
        if item.content_type == ContentType.CSV and not item.raw_data.startswith("http"):
            return self._local_csv_summary(item.raw_data)

        return await self._provider.process(
            item.content_type,
            item.raw_data,
            prompt,
            mime_type=item.mime_type,
        )

    @staticmethod
    def _local_csv_summary(raw: str) -> str:
        try:
            decoded = base64.b64decode(raw).decode("utf-8") if _is_base64(raw) else raw
            reader = csv.reader(io.StringIO(decoded))
            rows = list(reader)
            if not rows:
                return "[Empty CSV]"
            headers = rows[0]
            return f"CSV with {len(rows)-1} rows. Columns: {', '.join(headers)}"
        except Exception as exc:
            return f"[CSV parse error: {exc}]"


def _is_base64(s: str) -> bool:
    try:
        base64.b64decode(s, validate=True)
        return len(s) > 50
    except Exception:
        return False


# ---------------------------------------------------------------------------
# MessageProcessor — main entry point
# ---------------------------------------------------------------------------

class MessageProcessor:
    """Detects multi-modal content and returns an enriched text message."""

    def __init__(self, provider: Optional[LLMProvider] = None) -> None:
        self._provider = provider or FallbackProvider()
        self._extractor = ContentExtractor(self._provider)

    async def process(
        self,
        text: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> ProcessedMessage:
        items = _detect_content(text, attachments or [])

        if not items:
            return ProcessedMessage(
                original_text=text,
                enriched_text=text,
                detected_types=[ContentType.TEXT],
            )

        extractions: Dict[str, str] = {}
        for idx, item in enumerate(items):
            label = f"{item.content_type.value}_{idx}"
            try:
                extracted = await self._extractor.extract(item)
            except Exception as exc:
                logger.warning("Extraction failed for %s: %s", label, exc)
                extracted = f"[Extraction failed: {exc}]"
            extractions[label] = extracted

        context_block = "\n".join(
            f"--- Extracted from {k} ---\n{v}" for k, v in extractions.items()
        )
        enriched = f"{text}\n\n[Multi-modal context]\n{context_block}"

        return ProcessedMessage(
            original_text=text,
            enriched_text=enriched,
            detected_types=[i.content_type for i in items],
            extractions=extractions,
        )
