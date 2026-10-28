"""
Google AI Service — Gemini + Vertex AI + Workspace integration for Nautilus.

Capabilities:
  - GeminiClient: text, multimodal (image/audio/video), streaming
  - GoogleWorkspaceClient: Docs, Sheets, Drive (read/write)
  - GoogleSpeechClient: Speech-to-Text / Text-to-Speech
  - GoogleVisionClient: Vision API (object detection, OCR, label detection)

Authentication: uses service account JSON at GOOGLE_APPLICATION_CREDENTIALS
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

_SA_KEY_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.path.expanduser("~/nautilus-mvp/phase3/backend/google-sa-key.json"),
)
_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "chunxiao-vm-260330")
_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Gemini API key (from Google AI Studio / Vertex Express)
# Takes precedence over service account for Gemini LLM calls
_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Default models (google-genai SDK naming)
GEMINI_FLASH = "gemini-2.5-flash"     # latest fast model
GEMINI_PRO = "gemini-2.5-pro"         # most capable
GEMINI_NANO = "gemini-2.0-flash-lite" # smallest/cheapest


def _load_sa_credentials(scopes: Optional[List[str]] = None):
    """Load service account credentials from JSON key file."""
    try:
        from google.oauth2 import service_account as _sa
        default_scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
        ]
        return _sa.Credentials.from_service_account_file(
            _SA_KEY_PATH, scopes=scopes or default_scopes
        )
    except Exception as exc:
        logger.error("Failed to load Google SA credentials from %s: %s", _SA_KEY_PATH, exc)
        return None


# ------------------------------------------------------------------
# Gemini Client (Vertex AI)
# ------------------------------------------------------------------

class GeminiClient:
    """
    Gemini multimodal client.

    Uses google-genai SDK (API key auth) — simpler and more widely supported.
    Falls back to Vertex AI SDK if GEMINI_API_KEY is not set.

    Usage:
        client = GeminiClient()
        text = await client.chat("Hello Gemini")
        text = await client.analyze_image(b"...jpeg...", "What's in this image?")
        text = await client.transcribe_audio(b"...wav...", mime_type="audio/wav")
    """

    def __init__(self, model: str = GEMINI_FLASH):
        self._model_name = model

    def _get_client(self):
        """Return a configured google.genai Client."""
        from google.genai import Client as GenAIClient
        api_key = _GEMINI_API_KEY
        if api_key:
            return GenAIClient(api_key=api_key)
        # Fall back to service account via environment
        return GenAIClient()

    async def chat(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        max_tokens: int = 2048,
        model: Optional[str] = None,
    ) -> str:
        """Send a text prompt to Gemini and return the response."""
        def _sync():
            from google.genai import types as genai_types
            client = self._get_client()
            config = genai_types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                system_instruction=system,
            )
            contents = []
            for h in (history or []):
                role = "user" if h.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            response = client.models.generate_content(
                model=model or self._model_name,
                contents=contents,
                config=config,
            )
            return response.text

        return await asyncio.to_thread(_sync)

    async def analyze_image(
        self,
        image_data: Union[bytes, str],
        prompt: str = "Describe this image in detail.",
        *,
        mime_type: str = "image/jpeg",
        model: Optional[str] = None,
    ) -> str:
        """Analyze an image. image_data can be bytes or base64 string."""
        def _sync():
            from google.genai import types as genai_types
            client = self._get_client()

            if isinstance(image_data, str):
                raw = base64.b64decode(image_data)
            else:
                raw = image_data

            response = client.models.generate_content(
                model=model or self._model_name,
                contents=[
                    genai_types.Part.from_bytes(data=raw, mime_type=mime_type),
                    prompt,
                ],
            )
            return response.text

        return await asyncio.to_thread(_sync)

    async def analyze_video(
        self,
        video_data: Optional[bytes] = None,
        video_uri: Optional[str] = None,
        prompt: str = "Describe what happens in this video.",
        *,
        mime_type: str = "video/mp4",
        model: Optional[str] = None,
    ) -> str:
        """Analyze a video (bytes or GCS URI)."""
        def _sync():
            from google.genai import types as genai_types
            client = self._get_client()

            if video_uri:
                video_part = genai_types.Part.from_uri(
                    file_uri=video_uri, mime_type=mime_type
                )
            else:
                video_part = genai_types.Part.from_bytes(
                    data=video_data, mime_type=mime_type
                )
            response = client.models.generate_content(
                model=model or self._model_name,
                contents=[video_part, prompt],
            )
            return response.text

        return await asyncio.to_thread(_sync)

    async def transcribe_audio(
        self,
        audio_data: bytes,
        prompt: str = "Transcribe this audio to text.",
        *,
        mime_type: str = "audio/wav",
        model: Optional[str] = None,
    ) -> str:
        """Transcribe or analyze audio using Gemini."""
        def _sync():
            from google.genai import types as genai_types
            client = self._get_client()
            audio_part = genai_types.Part.from_bytes(data=audio_data, mime_type=mime_type)
            response = client.models.generate_content(
                model=model or self._model_name,
                contents=[audio_part, prompt],
            )
            return response.text

        return await asyncio.to_thread(_sync)

    async def generate_content_multimodal(
        self,
        parts: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> str:
        """
        General multimodal call.

        parts: list of dicts with keys:
          - {"type": "text", "text": "..."}
          - {"type": "image", "data": bytes, "mime_type": "image/jpeg"}
          - {"type": "audio", "data": bytes, "mime_type": "audio/wav"}
          - {"type": "video_uri", "uri": "gs://...", "mime_type": "video/mp4"}
        """
        def _sync():
            from google.genai import types as genai_types
            client = self._get_client()
            content = []
            for p in parts:
                t = p.get("type", "text")
                if t == "text":
                    content.append(p["text"])
                elif t in ("image", "audio", "video"):
                    content.append(genai_types.Part.from_bytes(
                        data=p["data"],
                        mime_type=p.get("mime_type", "image/jpeg"),
                    ))
                elif t == "video_uri":
                    content.append(genai_types.Part.from_uri(
                        file_uri=p["uri"],
                        mime_type=p.get("mime_type", "video/mp4"),
                    ))
            response = client.models.generate_content(
                model=model or self._model_name,
                contents=content,
                config=genai_types.GenerateContentConfig(max_output_tokens=max_tokens),
            )
            return response.text

        return await asyncio.to_thread(_sync)


# ------------------------------------------------------------------
# Google Speech Client
# ------------------------------------------------------------------

class GoogleSpeechClient:
    """
    Speech-to-Text and Text-to-Speech via Google Cloud.

    Usage:
        client = GoogleSpeechClient()
        text = await client.speech_to_text(audio_bytes, language="zh-CN")
        audio = await client.text_to_speech("你好世界", language="zh-CN")
    """

    async def speech_to_text(
        self,
        audio_data: bytes,
        *,
        language: str = "zh-CN",
        sample_rate: int = 16000,
        encoding: str = "LINEAR16",
    ) -> str:
        """Convert audio bytes to text."""
        def _sync():
            from google.cloud import speech
            creds = _load_sa_credentials(["https://www.googleapis.com/auth/cloud-platform"])
            client = speech.SpeechClient(credentials=creds)
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=getattr(speech.RecognitionConfig.AudioEncoding, encoding, 1),
                sample_rate_hertz=sample_rate,
                language_code=language,
                enable_automatic_punctuation=True,
            )
            response = client.recognize(config=config, audio=audio)
            return " ".join(r.alternatives[0].transcript for r in response.results)

        return await asyncio.to_thread(_sync)

    async def text_to_speech(
        self,
        text: str,
        *,
        language: str = "zh-CN",
        voice_name: Optional[str] = None,
        speaking_rate: float = 1.0,
    ) -> bytes:
        """Convert text to audio bytes (MP3)."""
        def _sync():
            from google.cloud import texttospeech
            creds = _load_sa_credentials(["https://www.googleapis.com/auth/cloud-platform"])
            client = texttospeech.TextToSpeechClient(credentials=creds)
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=language,
                name=voice_name or ("cmn-CN-Wavenet-A" if "zh" in language else "en-US-Wavenet-C"),
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
            )
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            return response.audio_content

        return await asyncio.to_thread(_sync)


# ------------------------------------------------------------------
# Google Vision Client
# ------------------------------------------------------------------

class GoogleVisionClient:
    """
    Cloud Vision API — object detection, OCR, label detection, etc.

    Usage:
        client = GoogleVisionClient()
        labels = await client.label_image(image_bytes)
        text = await client.extract_text(image_bytes)
        objects = await client.detect_objects(image_bytes)
    """

    async def label_image(self, image_data: bytes) -> List[str]:
        """Return top labels for an image."""
        def _sync():
            from google.cloud import vision
            creds = _load_sa_credentials(["https://www.googleapis.com/auth/cloud-platform"])
            client = vision.ImageAnnotatorClient(credentials=creds)
            image = vision.Image(content=image_data)
            response = client.label_detection(image=image)
            return [lbl.description for lbl in response.label_annotations]

        return await asyncio.to_thread(_sync)

    async def extract_text(self, image_data: bytes) -> str:
        """OCR: extract text from an image."""
        def _sync():
            from google.cloud import vision
            creds = _load_sa_credentials(["https://www.googleapis.com/auth/cloud-platform"])
            client = vision.ImageAnnotatorClient(credentials=creds)
            image = vision.Image(content=image_data)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            return texts[0].description if texts else ""

        return await asyncio.to_thread(_sync)

    async def detect_objects(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Detect objects with bounding boxes."""
        def _sync():
            from google.cloud import vision
            creds = _load_sa_credentials(["https://www.googleapis.com/auth/cloud-platform"])
            client = vision.ImageAnnotatorClient(credentials=creds)
            image = vision.Image(content=image_data)
            response = client.object_localization(image=image)
            return [
                {"name": obj.name, "score": round(obj.score, 3)}
                for obj in response.localized_object_annotations
            ]

        return await asyncio.to_thread(_sync)


# ------------------------------------------------------------------
# Google Workspace Client (Drive + Docs + Sheets)
# ------------------------------------------------------------------

class GoogleWorkspaceClient:
    """
    Google Workspace integration: Drive, Docs, Sheets.

    Note: Requires the service account to have access to specific files,
    OR for files to be shared with the service account email.

    Service account email: vertex-express@chunxiao-vm-260330.iam.gserviceaccount.com
    """

    _SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    def _build_service(self, service_name: str, version: str):
        from googleapiclient.discovery import build as gapi_build
        creds = _load_sa_credentials(self._SCOPES)
        return gapi_build(service_name, version, credentials=creds)

    # --- Drive ---

    async def list_files(
        self,
        query: str = "",
        page_size: int = 10,
    ) -> List[Dict[str, str]]:
        """List files in Drive accessible by the service account."""
        def _sync():
            svc = self._build_service("drive", "v3")
            results = svc.files().list(
                q=query or "trashed=false",
                pageSize=page_size,
                fields="files(id, name, mimeType, modifiedTime)",
            ).execute()
            return results.get("files", [])

        return await asyncio.to_thread(_sync)

    async def read_file(self, file_id: str) -> str:
        """Download and return text content of a Drive file."""
        def _sync():
            svc = self._build_service("drive", "v3")
            # Export as plain text
            content = svc.files().export(
                fileId=file_id, mimeType="text/plain"
            ).execute()
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="replace")
            return str(content)

        return await asyncio.to_thread(_sync)

    async def create_doc(self, title: str, content: str) -> Dict[str, str]:
        """Create a new Google Doc with text content."""
        def _sync():
            docs_svc = self._build_service("docs", "v1")
            # Create empty doc
            doc = docs_svc.documents().create(body={"title": title}).execute()
            doc_id = doc.get("documentId")
            # Insert content
            docs_svc.documents().batchUpdate(
                documentId=doc_id,
                body={
                    "requests": [{
                        "insertText": {
                            "location": {"index": 1},
                            "text": content,
                        }
                    }]
                },
            ).execute()
            return {
                "document_id": doc_id,
                "title": title,
                "url": f"https://docs.google.com/document/d/{doc_id}/edit",
            }

        return await asyncio.to_thread(_sync)

    # --- Sheets ---

    async def read_sheet(
        self,
        spreadsheet_id: str,
        range_: str = "Sheet1!A1:Z1000",
    ) -> List[List[str]]:
        """Read values from a Google Sheet."""
        def _sync():
            svc = self._build_service("sheets", "v4")
            result = svc.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_,
            ).execute()
            return result.get("values", [])

        return await asyncio.to_thread(_sync)

    async def write_sheet(
        self,
        spreadsheet_id: str,
        range_: str,
        values: List[List[Any]],
    ) -> Dict[str, Any]:
        """Write values to a Google Sheet."""
        def _sync():
            svc = self._build_service("sheets", "v4")
            result = svc.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption="USER_ENTERED",
                body={"values": values},
            ).execute()
            return {
                "updated_cells": result.get("updatedCells"),
                "updated_range": result.get("updatedRange"),
            }

        return await asyncio.to_thread(_sync)

    async def create_sheet(self, title: str) -> Dict[str, str]:
        """Create a new Google Spreadsheet."""
        def _sync():
            svc = self._build_service("sheets", "v4")
            spreadsheet = svc.spreadsheets().create(
                body={"properties": {"title": title}},
                fields="spreadsheetId,spreadsheetUrl",
            ).execute()
            return {
                "spreadsheet_id": spreadsheet.get("spreadsheetId"),
                "url": spreadsheet.get("spreadsheetUrl"),
                "title": title,
            }

        return await asyncio.to_thread(_sync)


# ------------------------------------------------------------------
# Module-level singletons
# ------------------------------------------------------------------

_gemini: Optional[GeminiClient] = None
_speech: Optional[GoogleSpeechClient] = None
_vision: Optional[GoogleVisionClient] = None
_workspace: Optional[GoogleWorkspaceClient] = None


def get_gemini(model: str = GEMINI_FLASH) -> GeminiClient:
    global _gemini
    if _gemini is None:
        _gemini = GeminiClient(model=model)
    return _gemini


def get_speech_client() -> GoogleSpeechClient:
    global _speech
    if _speech is None:
        _speech = GoogleSpeechClient()
    return _speech


def get_vision_client() -> GoogleVisionClient:
    global _vision
    if _vision is None:
        _vision = GoogleVisionClient()
    return _vision


def get_workspace_client() -> GoogleWorkspaceClient:
    global _workspace
    if _workspace is None:
        _workspace = GoogleWorkspaceClient()
    return _workspace
