"""
Multimodal Task API — image analysis, audio transcription, TTS, document analysis,
image generation, and vector embeddings.

POST /api/multimodal/image-analysis     — Upload image, get AI analysis
POST /api/multimodal/audio-transcribe   — Upload audio, get transcription + summary
POST /api/multimodal/tts                — Convert text to speech (MiniMax TTS)
POST /api/multimodal/document-analysis  — Upload PDF/image document, get analysis
POST /api/multimodal/image-generate     — Generate image from text (Imagen 4)
POST /api/multimodal/embed              — Generate vector embedding (Gemini Embedding)
GET  /api/multimodal/tts/{task_id}      — Download generated audio file
GET  /api/multimodal/image/{task_id}    — Download generated image
"""
import base64
import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text

from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/multimodal", tags=["Multimodal"])

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
MINIMAX_TTS_MODEL = "speech-2.8-hd"  # MiniMax Speech 2.8 (100K chars/day)


# ========== 1. Image Analysis ==========

@router.post("/image-analysis")
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this image in detail and extract any text or data visible."),
    db: Session = Depends(get_db),
):
    """Upload an image for AI analysis using Gemini Vision."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image (JPEG, PNG, etc.)")

    image_data = await file.read()
    if len(image_data) > 20 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 20MB)")

    task_id = f"mm_img_{uuid.uuid4().hex[:8]}"

    # Save task record
    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'image_analysis', 'in_progress', 2)"
    ), {"tid": task_id, "title": f"Image Analysis: {file.filename}", "desc": prompt})
    db.commit()

    try:
        from services.google_ai import GeminiClient
        client = GeminiClient()
        result = await client.analyze_image(image_data, prompt, mime_type=file.content_type)

        db.execute(text(
            "UPDATE academic_tasks SET status='completed', result_output=:result, updated_at=NOW() "
            "WHERE task_id=:tid"
        ), {"result": result, "tid": task_id})
        db.commit()

        return {"success": True, "data": {"task_id": task_id, "analysis": result}}
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"Image analysis failed: {str(e)[:200]}")


# ========== 2. Audio Transcription ==========

@router.post("/audio-transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    prompt: str = Form("Transcribe this audio to text. Then provide a brief summary."),
    db: Session = Depends(get_db),
):
    """Upload audio for transcription + summary using Gemini or MiniMax."""
    allowed = {"audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/webm", "audio/m4a"}
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(400, f"Unsupported audio format. Allowed: {allowed}")

    audio_data = await file.read()
    if len(audio_data) > 50 * 1024 * 1024:
        raise HTTPException(400, "Audio too large (max 50MB)")

    task_id = f"mm_audio_{uuid.uuid4().hex[:8]}"

    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'audio_transcription', 'in_progress', 3)"
    ), {"tid": task_id, "title": f"Audio Transcription: {file.filename}", "desc": prompt})
    db.commit()

    try:
        from services.google_ai import GeminiClient
        client = GeminiClient()
        mime = file.content_type or "audio/wav"
        result = await client.transcribe_audio(audio_data, prompt, mime_type=mime)

        db.execute(text(
            "UPDATE academic_tasks SET status='completed', result_output=:result, updated_at=NOW() "
            "WHERE task_id=:tid"
        ), {"result": result, "tid": task_id})
        db.commit()

        return {"success": True, "data": {"task_id": task_id, "transcription": result}}
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"Transcription failed: {str(e)[:200]}")


# ========== 3. Text-to-Speech (Gemini TTS) ==========

@router.post("/tts")
async def text_to_speech(
    text_content: str = Form(..., alias="text"),
    voice: str = Form("Kore"),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """Convert text to speech using Gemini TTS (free)."""
    if len(text_content) > 10000:
        raise HTTPException(400, "Text too long (max 10000 chars)")

    task_id = f"mm_tts_{uuid.uuid4().hex[:8]}"

    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'tts_generation', 'in_progress', 1)"
    ), {"tid": task_id, "title": f"TTS: {text_content[:50]}...", "desc": text_content[:200]})
    db.commit()

    try:
        import asyncio

        def _gemini_tts():
            from google import genai
            from google.genai import types
            gemini_key = os.getenv("GEMINI_API_KEY", "")
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=text_content,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                        )
                    ),
                ),
            )
            return response.candidates[0].content.parts[0].inline_data.data

        audio_data = await asyncio.to_thread(_gemini_tts)

        # Save audio file (PCM WAV from Gemini)
        audio_path = f"/tmp/nautilus_tts_{task_id}.wav"
        with open(audio_path, "wb") as f:
            f.write(audio_data)

        size_kb = len(audio_data) // 1024
        db.execute(text(
            "UPDATE academic_tasks SET status='completed', "
            "result_output=:result, updated_at=NOW() WHERE task_id=:tid"
        ), {"result": f"Audio generated: {audio_path} ({size_kb}KB)", "tid": task_id})
        db.commit()

        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "audio_url": f"/api/multimodal/tts/{task_id}",
                "size_kb": size_kb,
            }
        }
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"TTS failed: {str(e)[:200]}")


@router.get("/tts/{task_id}")
async def get_tts_audio(task_id: str):
    """Download generated TTS audio file."""
    from fastapi.responses import FileResponse
    for ext in ["wav", "mp3"]:
        audio_path = f"/tmp/nautilus_tts_{task_id}.{ext}"
        if os.path.exists(audio_path):
            media = "audio/wav" if ext == "wav" else "audio/mpeg"
            return FileResponse(audio_path, media_type=media, filename=f"{task_id}.{ext}")
    raise HTTPException(404, "Audio file not found")


# ========== 4. Document Analysis ==========

@router.post("/document-analysis")
async def analyze_document(
    file: UploadFile = File(...),
    prompt: str = Form("Analyze this document. Extract key information, summarize content, and highlight important data points."),
    db: Session = Depends(get_db),
):
    """Upload PDF or image document for AI analysis."""
    allowed_types = {
        "application/pdf": "application/pdf",
        "image/jpeg": "image/jpeg",
        "image/png": "image/png",
        "image/tiff": "image/tiff",
    }

    content_type = file.content_type or "application/pdf"
    if content_type not in allowed_types:
        raise HTTPException(400, "Unsupported format. Allowed: PDF, JPEG, PNG, TIFF")

    file_data = await file.read()
    if len(file_data) > 30 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 30MB)")

    task_id = f"mm_doc_{uuid.uuid4().hex[:8]}"

    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'document_analysis', 'in_progress', 3)"
    ), {"tid": task_id, "title": f"Document Analysis: {file.filename}", "desc": prompt})
    db.commit()

    try:
        from services.google_ai import GeminiClient
        client = GeminiClient()

        if content_type == "application/pdf":
            # Gemini can handle PDFs directly via bytes
            result = await client.analyze_image(file_data, prompt, mime_type="application/pdf")
        else:
            result = await client.analyze_image(file_data, prompt, mime_type=content_type)

        db.execute(text(
            "UPDATE academic_tasks SET status='completed', result_output=:result, updated_at=NOW() "
            "WHERE task_id=:tid"
        ), {"result": result, "tid": task_id})
        db.commit()

        return {"success": True, "data": {"task_id": task_id, "analysis": result}}
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"Document analysis failed: {str(e)[:200]}")


# ========== 5. Image Generation (Imagen 4) ==========

@router.post("/image-generate")
async def generate_image(
    prompt: str = Form(...),
    style: str = Form("photorealistic"),
    db: Session = Depends(get_db),
):
    """Generate images using Google Imagen 4."""
    import asyncio
    task_id = f"mm_img_gen_{uuid.uuid4().hex[:8]}"

    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'image_generation', 'in_progress', 2)"
    ), {"tid": task_id, "title": f"Image Gen: {prompt[:50]}", "desc": prompt})
    db.commit()

    try:
        def _gen():
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            full_prompt = f"{prompt}, {style} style" if style != "photorealistic" else prompt
            result = client.models.generate_images(
                model="imagen-4.0-fast-generate-001",
                prompt=full_prompt,
                config=types.GenerateImagesConfig(number_of_images=1),
            )
            return result.generated_images[0].image.image_bytes

        img_bytes = await asyncio.to_thread(_gen)
        img_path = f"/tmp/nautilus_img_{task_id}.png"
        with open(img_path, "wb") as f:
            f.write(img_bytes)

        size_kb = len(img_bytes) // 1024
        db.execute(text(
            "UPDATE academic_tasks SET status='completed', result_output=:r, updated_at=NOW() WHERE task_id=:tid"
        ), {"r": f"Image generated: {img_path} ({size_kb}KB)", "tid": task_id})
        db.commit()

        return {"success": True, "data": {"task_id": task_id, "image_url": f"/api/multimodal/image/{task_id}", "size_kb": size_kb}}
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"Image generation failed: {str(e)[:200]}")


@router.get("/image/{task_id}")
async def get_generated_image(task_id: str):
    """Download generated image."""
    from fastapi.responses import FileResponse
    img_path = f"/tmp/nautilus_img_{task_id}.png"
    if not os.path.exists(img_path):
        raise HTTPException(404, "Image not found")
    return FileResponse(img_path, media_type="image/png", filename=f"{task_id}.png")


# ========== 6. Vector Embedding ==========

@router.post("/embed")
async def generate_embedding(
    text_content: str = Form(..., alias="text"),
):
    """Generate vector embedding using Gemini Embedding (3072 dimensions)."""
    import asyncio
    try:
        def _embed():
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            result = client.models.embed_content(model="gemini-embedding-001", contents=text_content)
            return result.embeddings[0].values

        vector = await asyncio.to_thread(_embed)
        return {"success": True, "data": {"dimensions": len(vector), "embedding": vector[:10], "full_length": len(vector)}}
    except Exception as e:
        raise HTTPException(500, f"Embedding failed: {str(e)[:200]}")


# ========== 7. MiniMax Image Generation (image-01) ==========

@router.post("/minimax-image")
async def minimax_image_generate(
    prompt: str = Form(...),
    aspect_ratio: str = Form("1:1"),
    db: Session = Depends(get_db),
):
    """Generate image using MiniMax image-01 (200 images/day)."""
    import asyncio, httpx

    if not MINIMAX_API_KEY:
        raise HTTPException(503, "MiniMax API key not configured")

    task_id = f"mm_mxi_{uuid.uuid4().hex[:8]}"

    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'minimax_image', 'in_progress', 2)"
    ), {"tid": task_id, "title": f"MiniMax Image: {prompt[:50]}", "desc": prompt})
    db.commit()

    try:
        def _gen():
            r = httpx.post(
                f"{MINIMAX_BASE_URL}/image/generation",
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
                json={"model": "image-01", "prompt": prompt, "aspect_ratio": aspect_ratio},
                timeout=60,
            )
            r.raise_for_status()
            ct = r.headers.get("content-type", "")
            if "image" in ct:
                return r.content
            # Some responses return JSON with base64
            data = r.json()
            if data.get("data", {}).get("image"):
                return base64.b64decode(data["data"]["image"])
            raise ValueError(f"Unexpected response: {r.text[:200]}")

        img_bytes = await asyncio.to_thread(_gen)
        img_path = f"/tmp/nautilus_mxi_{task_id}.png"
        with open(img_path, "wb") as f:
            f.write(img_bytes)

        size_kb = len(img_bytes) // 1024
        db.execute(text(
            "UPDATE academic_tasks SET status='completed', result_output=:r, updated_at=NOW() WHERE task_id=:tid"
        ), {"r": f"MiniMax image: {img_path} ({size_kb}KB)", "tid": task_id})
        db.commit()

        return {"success": True, "data": {"task_id": task_id, "image_url": f"/api/multimodal/minimax-image/{task_id}", "size_kb": size_kb, "provider": "minimax-image-01"}}
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"MiniMax image generation failed: {str(e)[:200]}")


@router.get("/minimax-image/{task_id}")
async def get_minimax_image(task_id: str):
    """Download MiniMax generated image."""
    from fastapi.responses import FileResponse
    img_path = f"/tmp/nautilus_mxi_{task_id}.png"
    if not os.path.exists(img_path):
        raise HTTPException(404, "Image not found")
    return FileResponse(img_path, media_type="image/png", filename=f"{task_id}.png")


# ========== 8. MiniMax TTS (Speech 2.8 HD) ==========

@router.post("/minimax-tts")
async def minimax_tts(
    text_content: str = Form(..., alias="text"),
    voice_id: str = Form("female-shaonv"),
    model: str = Form("speech-2.8-hd"),
    db: Session = Depends(get_db),
):
    """MiniMax TTS — higher quality Chinese voices (100K chars/day)."""
    import asyncio, httpx

    if not MINIMAX_API_KEY:
        raise HTTPException(503, "MiniMax API key not configured")
    if len(text_content) > 10000:
        raise HTTPException(400, "Text too long (max 10000 chars)")

    task_id = f"mm_mxt_{uuid.uuid4().hex[:8]}"

    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'minimax_tts', 'in_progress', 1)"
    ), {"tid": task_id, "title": f"MiniMax TTS: {text_content[:50]}", "desc": text_content[:200]})
    db.commit()

    try:
        def _tts():
            r = httpx.post(
                f"{MINIMAX_BASE_URL}/t2a_v2",
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "text": text_content,
                    "voice_setting": {"voice_id": voice_id},
                    "audio_setting": {"format": "mp3", "sample_rate": 32000},
                },
                timeout=30,
            )
            d = r.json()
            status_code = d.get("base_resp", {}).get("status_code", -1)
            if status_code != 0:
                raise ValueError(f"MiniMax TTS error: {d.get('base_resp', {}).get('status_msg', 'unknown')}")
            audio_b64 = d.get("data", {}).get("audio", "")
            if not audio_b64:
                raise ValueError("No audio data returned")
            return base64.b64decode(audio_b64)

        audio_bytes = await asyncio.to_thread(_tts)
        audio_path = f"/tmp/nautilus_tts_{task_id}.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        size_kb = len(audio_bytes) // 1024
        db.execute(text(
            "UPDATE academic_tasks SET status='completed', result_output=:r, updated_at=NOW() WHERE task_id=:tid"
        ), {"r": f"MiniMax TTS: {audio_path} ({size_kb}KB)", "tid": task_id})
        db.commit()

        return {"success": True, "data": {"task_id": task_id, "audio_url": f"/api/multimodal/tts/{task_id}", "size_kb": size_kb, "provider": f"minimax-{model}"}}
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"MiniMax TTS failed: {str(e)[:200]}")


# ========== 9. MiniMax Video Generation (Hailuo) ==========

@router.post("/minimax-video")
async def minimax_video_generate(
    prompt: str = Form(...),
    model: str = Form("Hailuo-2.3-Fast"),
    db: Session = Depends(get_db),
):
    """Generate video using MiniMax Hailuo. Returns task_id for async polling."""
    import asyncio, httpx

    if not MINIMAX_API_KEY:
        raise HTTPException(503, "MiniMax API key not configured")

    task_id = f"mm_mxv_{uuid.uuid4().hex[:8]}"

    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'minimax_video', 'in_progress', 5)"
    ), {"tid": task_id, "title": f"MiniMax Video: {prompt[:50]}", "desc": prompt})
    db.commit()

    try:
        def _submit():
            r = httpx.post(
                f"{MINIMAX_BASE_URL}/video_generation",
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "prompt": prompt},
                timeout=30,
            )
            return r.json()

        result = await asyncio.to_thread(_submit)
        generation_id = result.get("task_id") or result.get("data", {}).get("task_id", "")

        db.execute(text(
            "UPDATE academic_tasks SET result_output=:r, updated_at=NOW() WHERE task_id=:tid"
        ), {"r": f"Video generation submitted: {generation_id}", "tid": task_id})
        db.commit()

        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "minimax_task_id": generation_id,
                "status": "generating",
                "provider": f"minimax-{model}",
                "note": "Video generation is async. Poll /api/multimodal/minimax-video-status/{minimax_task_id} for result.",
            }
        }
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"Video generation failed: {str(e)[:200]}")


@router.get("/minimax-video-status/{minimax_task_id}")
async def minimax_video_status(minimax_task_id: str):
    """Poll MiniMax video generation status."""
    import httpx
    try:
        r = httpx.get(
            f"{MINIMAX_BASE_URL}/query/video_generation",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
            params={"task_id": minimax_task_id},
            timeout=15,
        )
        return {"success": True, "data": r.json()}
    except Exception as e:
        raise HTTPException(500, f"Status check failed: {str(e)[:200]}")


# ========== 10. MiniMax Music Generation (Mu) ==========

@router.post("/minimax-music")
async def minimax_music_generate(
    prompt: str = Form(...),
    duration_seconds: int = Form(30),
    model: str = Form("Mu-2.5"),
    db: Session = Depends(get_db),
):
    """Generate music using MiniMax Mu-2.5."""
    import asyncio, httpx

    if not MINIMAX_API_KEY:
        raise HTTPException(503, "MiniMax API key not configured")
    if duration_seconds > 300:
        raise HTTPException(400, "Duration too long (max 300s)")

    task_id = f"mm_mxm_{uuid.uuid4().hex[:8]}"

    db.execute(text(
        "INSERT INTO academic_tasks (task_id, title, description, task_type, status, token_reward) "
        "VALUES (:tid, :title, :desc, 'minimax_music', 'in_progress', 3)"
    ), {"tid": task_id, "title": f"MiniMax Music: {prompt[:50]}", "desc": prompt})
    db.commit()

    try:
        def _gen():
            r = httpx.post(
                f"{MINIMAX_BASE_URL}/music_generation",
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "prompt": prompt, "duration_seconds": duration_seconds},
                timeout=60,
            )
            return r.json()

        result = await asyncio.to_thread(_gen)
        generation_id = result.get("task_id") or result.get("data", {}).get("task_id", "")

        db.execute(text(
            "UPDATE academic_tasks SET result_output=:r, updated_at=NOW() WHERE task_id=:tid"
        ), {"r": f"Music generation submitted: {generation_id}", "tid": task_id})
        db.commit()

        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "minimax_task_id": generation_id,
                "status": "generating",
                "provider": f"minimax-{model}",
                "note": "Music generation is async. Poll /api/multimodal/minimax-music-status/{minimax_task_id} for result.",
            }
        }
    except Exception as e:
        db.execute(text(
            "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
        ), {"err": str(e)[:500], "tid": task_id})
        db.commit()
        raise HTTPException(500, f"Music generation failed: {str(e)[:200]}")


@router.get("/minimax-music-status/{minimax_task_id}")
async def minimax_music_status(minimax_task_id: str):
    """Poll MiniMax music generation status."""
    import httpx
    try:
        r = httpx.get(
            f"{MINIMAX_BASE_URL}/query/music_generation",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
            params={"task_id": minimax_task_id},
            timeout=15,
        )
        return {"success": True, "data": r.json()}
    except Exception as e:
        raise HTTPException(500, f"Status check failed: {str(e)[:200]}")
