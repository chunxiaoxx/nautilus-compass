"""
Google AI API — Gemini + Vision + Speech + Workspace endpoints.

Routes:
  POST /api/google/chat           — Gemini text chat
  POST /api/google/analyze-image  — Image analysis (Vision + Gemini)
  POST /api/google/transcribe     — Speech-to-Text
  POST /api/google/tts            — Text-to-Speech
  POST /api/google/multimodal     — General multimodal call
  GET  /api/google/workspace/files — List Drive files
  POST /api/google/workspace/docs  — Create Google Doc
  GET  /api/google/workspace/sheet/{id} — Read Sheet
  POST /api/google/workspace/sheet/{id} — Write Sheet
  GET  /api/google/status          — Service health
"""
import base64
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google", tags=["Google AI"])


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    system: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    model: Optional[str] = None
    max_tokens: int = Field(2048, le=8192)


class ImageAnalysisRequest(BaseModel):
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    prompt: str = "请详细描述这张图片的内容。"
    mime_type: str = "image/jpeg"
    use_vision_api: bool = False    # True → Cloud Vision, False → Gemini


class TTSRequest(BaseModel):
    text: str = Field(..., max_length=5000)
    language: str = "zh-CN"
    voice_name: Optional[str] = None
    speaking_rate: float = Field(1.0, ge=0.25, le=4.0)


class MultimodalRequest(BaseModel):
    parts: List[Dict[str, Any]]
    model: Optional[str] = None
    max_tokens: int = Field(2048, le=8192)


class DocCreateRequest(BaseModel):
    title: str
    content: str


class SheetWriteRequest(BaseModel):
    range_: str = Field(..., alias="range")
    values: List[List[Any]]


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

@router.get("/status")
async def google_ai_status():
    """Check which Google AI services are available."""
    import os
    sa_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        os.path.expanduser("~/nautilus-mvp/phase3/backend/google-sa-key.json"),
    )

    services: Dict[str, str] = {}

    try:
        import vertexai  # noqa
        services["vertexai"] = "available"
    except ImportError:
        services["vertexai"] = "not_installed"

    try:
        from google.cloud import speech  # noqa
        services["speech_to_text"] = "available"
    except ImportError:
        services["speech_to_text"] = "not_installed"

    try:
        from google.cloud import texttospeech  # noqa
        services["text_to_speech"] = "available"
    except ImportError:
        services["text_to_speech"] = "not_installed"

    try:
        from google.cloud import vision  # noqa
        services["vision"] = "available"
    except ImportError:
        services["vision"] = "not_installed"

    try:
        from googleapiclient.discovery import build  # noqa
        services["workspace"] = "available"
    except ImportError:
        services["workspace"] = "not_installed"

    return {
        "success": True,
        "data": {
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "chunxiao-vm-260330"),
            "sa_key_exists": os.path.exists(sa_path),
            "services": services,
        },
    }


# ------------------------------------------------------------------
# Gemini Chat
# ------------------------------------------------------------------

@router.post("/chat")
async def gemini_chat(body: ChatRequest):
    """Send a text message to Gemini and get a response."""
    try:
        from services.google_ai import get_gemini
        gemini = get_gemini()
        response = await gemini.chat(
            body.message,
            system=body.system,
            history=body.history,
            max_tokens=body.max_tokens,
            model=body.model,
        )
        return {"success": True, "data": {"response": response, "model": body.model or "gemini-2.0-flash-001"}}
    except Exception as exc:
        logger.error("Gemini chat error: %s", exc)
        raise HTTPException(500, f"Gemini error: {exc}")


# ------------------------------------------------------------------
# Image Analysis
# ------------------------------------------------------------------

@router.post("/analyze-image")
async def analyze_image(body: ImageAnalysisRequest):
    """
    Analyze an image using Gemini Vision or Cloud Vision API.

    Send either image_base64 or image_url.
    """
    if not body.image_base64 and not body.image_url:
        raise HTTPException(400, "Provide image_base64 or image_url")

    try:
        if body.use_vision_api and body.image_base64:
            # Use Cloud Vision API for structured detection
            from services.google_ai import get_vision_client
            vc = get_vision_client()
            img_bytes = base64.b64decode(body.image_base64)
            labels = await vc.label_image(img_bytes)
            text = await vc.extract_text(img_bytes)
            objects = await vc.detect_objects(img_bytes)
            return {
                "success": True,
                "data": {
                    "labels": labels,
                    "text": text,
                    "objects": objects,
                    "provider": "cloud_vision",
                },
            }
        else:
            # Use Gemini Vision
            from services.google_ai import get_gemini
            gemini = get_gemini()
            if body.image_base64:
                result = await gemini.analyze_image(
                    body.image_base64, body.prompt, mime_type=body.mime_type
                )
            else:
                # Download from URL
                import httpx
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(body.image_url)
                    img_bytes = resp.content
                result = await gemini.analyze_image(
                    img_bytes, body.prompt, mime_type=body.mime_type
                )
            return {"success": True, "data": {"description": result, "provider": "gemini"}}

    except Exception as exc:
        logger.error("Image analysis error: %s", exc)
        raise HTTPException(500, f"Image analysis failed: {exc}")


@router.post("/analyze-image/upload")
async def analyze_image_upload(
    file: UploadFile = File(...),
    prompt: str = Form("请详细描述这张图片的内容。"),
):
    """Upload an image file for Gemini Vision analysis."""
    try:
        img_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        from services.google_ai import get_gemini
        gemini = get_gemini()
        result = await gemini.analyze_image(img_bytes, prompt, mime_type=mime_type)
        return {"success": True, "data": {"description": result, "filename": file.filename}}
    except Exception as exc:
        logger.error("Image upload analysis error: %s", exc)
        raise HTTPException(500, f"Analysis failed: {exc}")


# ------------------------------------------------------------------
# Audio: Speech-to-Text
# ------------------------------------------------------------------

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("zh-CN"),
    use_gemini: bool = Form(False),
):
    """
    Transcribe audio to text.

    use_gemini=True → use Gemini multimodal (handles more formats)
    use_gemini=False → use Cloud Speech-to-Text (more accurate for pure audio)
    """
    try:
        audio_bytes = await file.read()
        mime_type = file.content_type or "audio/wav"

        if use_gemini:
            from services.google_ai import get_gemini
            gemini = get_gemini()
            result = await gemini.transcribe_audio(
                audio_bytes,
                f"Transcribe this audio to {language} text.",
                mime_type=mime_type,
            )
        else:
            from services.google_ai import get_speech_client
            sc = get_speech_client()
            result = await sc.speech_to_text(audio_bytes, language=language)

        return {"success": True, "data": {"transcript": result, "language": language}}
    except Exception as exc:
        logger.error("Transcription error: %s", exc)
        raise HTTPException(500, f"Transcription failed: {exc}")


# ------------------------------------------------------------------
# Text-to-Speech
# ------------------------------------------------------------------

@router.post("/tts")
async def text_to_speech(body: TTSRequest):
    """Convert text to speech. Returns MP3 audio bytes as base64."""
    try:
        from services.google_ai import get_speech_client
        sc = get_speech_client()
        audio_bytes = await sc.text_to_speech(
            body.text,
            language=body.language,
            voice_name=body.voice_name,
            speaking_rate=body.speaking_rate,
        )
        audio_b64 = base64.b64encode(audio_bytes).decode()
        return {
            "success": True,
            "data": {
                "audio_base64": audio_b64,
                "mime_type": "audio/mp3",
                "language": body.language,
            },
        }
    except Exception as exc:
        logger.error("TTS error: %s", exc)
        raise HTTPException(500, f"TTS failed: {exc}")


@router.post("/tts/stream")
async def text_to_speech_stream(body: TTSRequest):
    """Convert text to speech. Returns raw MP3 audio for direct playback."""
    try:
        from services.google_ai import get_speech_client
        sc = get_speech_client()
        audio_bytes = await sc.text_to_speech(
            body.text,
            language=body.language,
            voice_name=body.voice_name,
            speaking_rate=body.speaking_rate,
        )
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as exc:
        logger.error("TTS stream error: %s", exc)
        raise HTTPException(500, f"TTS failed: {exc}")


# ------------------------------------------------------------------
# General Multimodal
# ------------------------------------------------------------------

@router.post("/multimodal")
async def multimodal_call(body: MultimodalRequest):
    """
    General multimodal Gemini call.

    parts format:
      [{"type": "text", "text": "What is this?"},
       {"type": "image", "data": "<base64>", "mime_type": "image/jpeg"},
       {"type": "audio", "data": "<base64>", "mime_type": "audio/wav"}]
    """
    try:
        # Decode base64 data fields
        decoded_parts = []
        for p in body.parts:
            if p.get("type") in ("image", "audio", "video") and "data" in p:
                decoded_parts.append({
                    **p,
                    "data": base64.b64decode(p["data"]),
                })
            else:
                decoded_parts.append(p)

        from services.google_ai import get_gemini
        gemini = get_gemini()
        result = await gemini.generate_content_multimodal(
            decoded_parts,
            model=body.model,
            max_tokens=body.max_tokens,
        )
        return {"success": True, "data": {"response": result}}
    except Exception as exc:
        logger.error("Multimodal error: %s", exc)
        raise HTTPException(500, f"Multimodal call failed: {exc}")


# ------------------------------------------------------------------
# Google Workspace — Drive
# ------------------------------------------------------------------

@router.get("/workspace/files")
async def list_drive_files(query: str = "", limit: int = 10):
    """List Google Drive files accessible by the service account."""
    try:
        from services.google_ai import get_workspace_client
        ws = get_workspace_client()
        files = await ws.list_files(query=query, page_size=limit)
        return {"success": True, "data": {"files": files, "count": len(files)}}
    except Exception as exc:
        logger.error("Drive list error: %s", exc)
        raise HTTPException(500, f"Drive error: {exc}")


@router.get("/workspace/files/{file_id}")
async def read_drive_file(file_id: str):
    """Read text content of a Google Drive file."""
    try:
        from services.google_ai import get_workspace_client
        ws = get_workspace_client()
        content = await ws.read_file(file_id)
        return {"success": True, "data": {"content": content, "file_id": file_id}}
    except Exception as exc:
        logger.error("Drive read error: %s", exc)
        raise HTTPException(500, f"Drive read failed: {exc}")


# ------------------------------------------------------------------
# Google Workspace — Docs
# ------------------------------------------------------------------

@router.post("/workspace/docs")
async def create_doc(body: DocCreateRequest):
    """Create a new Google Doc with the given title and content."""
    try:
        from services.google_ai import get_workspace_client
        ws = get_workspace_client()
        result = await ws.create_doc(body.title, body.content)
        return {"success": True, "data": result}
    except Exception as exc:
        logger.error("Docs create error: %s", exc)
        raise HTTPException(500, f"Docs creation failed: {exc}")


# ------------------------------------------------------------------
# Google Workspace — Sheets
# ------------------------------------------------------------------

@router.get("/workspace/sheets/{spreadsheet_id}")
async def read_sheet(spreadsheet_id: str, range_: str = "Sheet1!A1:Z100"):
    """Read data from a Google Sheet."""
    try:
        from services.google_ai import get_workspace_client
        ws = get_workspace_client()
        data = await ws.read_sheet(spreadsheet_id, range_)
        return {
            "success": True,
            "data": {"values": data, "rows": len(data), "spreadsheet_id": spreadsheet_id},
        }
    except Exception as exc:
        logger.error("Sheets read error: %s", exc)
        raise HTTPException(500, f"Sheets read failed: {exc}")


@router.post("/workspace/sheets/{spreadsheet_id}")
async def write_sheet(spreadsheet_id: str, body: SheetWriteRequest):
    """Write data to a Google Sheet."""
    try:
        from services.google_ai import get_workspace_client
        ws = get_workspace_client()
        result = await ws.write_sheet(spreadsheet_id, body.range_, body.values)
        return {"success": True, "data": result}
    except Exception as exc:
        logger.error("Sheets write error: %s", exc)
        raise HTTPException(500, f"Sheets write failed: {exc}")


@router.post("/workspace/sheets")
async def create_sheet(title: str):
    """Create a new Google Spreadsheet."""
    try:
        from services.google_ai import get_workspace_client
        ws = get_workspace_client()
        result = await ws.create_sheet(title)
        return {"success": True, "data": result}
    except Exception as exc:
        logger.error("Sheets create error: %s", exc)
        raise HTTPException(500, f"Sheet creation failed: {exc}")
