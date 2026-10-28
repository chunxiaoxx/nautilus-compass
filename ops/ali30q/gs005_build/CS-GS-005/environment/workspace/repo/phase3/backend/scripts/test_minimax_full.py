#!/usr/bin/env python3
"""Test all MiniMax Token Plan capabilities."""
import os, sys, base64, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
import httpx

KEY = os.getenv("MINIMAX_API_KEY", "")
BASE = "https://api.minimaxi.com"

def test_tts():
    print("=== Speech 2.8 TTS ===")
    for model in ["speech-2.8", "speech-2.8-hd", "speech-02-hd", "speech-01-turbo"]:
        try:
            r = httpx.post(f"{BASE}/v1/t2a_v2",
                headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                json={"model": model, "text": "今日创投要闻", "voice_setting": {"voice_id": "female-shaonv"}, "audio_setting": {"format": "mp3", "sample_rate": 32000}},
                timeout=20)
            d = r.json()
            status = d.get("base_resp", {}).get("status_code", -1)
            has_audio = bool(d.get("data", {}).get("audio"))
            print(f"  {model}: status={status} audio={has_audio}")
            if has_audio:
                audio = base64.b64decode(d["data"]["audio"])
                with open(f"/tmp/minimax_tts_{model}.mp3", "wb") as f:
                    f.write(audio)
                print(f"  SAVED: {len(audio)//1024}KB")
                return model
        except Exception as e:
            print(f"  {model}: error {e}")
    return None

def test_image():
    print("\n=== image-01 ===")
    try:
        r = httpx.post(f"{BASE}/v1/image/generation",
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
            json={"model": "image-01", "prompt": "A futuristic AI agent marketplace, cyberpunk style"},
            timeout=60)
        ct = r.headers.get("content-type", "")
        print(f"  content-type: {ct}, status: {r.status_code}")
        if "image" in ct:
            with open("/tmp/minimax_image.png", "wb") as f:
                f.write(r.content)
            print(f"  OK: {len(r.content)//1024}KB")
            return True
        else:
            print(f"  response: {r.text[:300]}")
    except Exception as e:
        print(f"  error: {e}")
    return False

def test_video():
    print("\n=== Hailuo Video ===")
    try:
        r = httpx.post(f"{BASE}/v1/video_generation",
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
            json={"model": "Hailuo-2.3-Fast", "prompt": "AI agents collaborating on holographic display"},
            timeout=15)
        print(f"  status: {r.status_code}")
        print(f"  body: {r.text[:300]}")
    except Exception as e:
        print(f"  error: {e}")

def test_music():
    print("\n=== Mu-2.5 Music ===")
    try:
        r = httpx.post(f"{BASE}/v1/music_generation",
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
            json={"model": "Mu-2.5", "prompt": "calm ambient electronic", "duration_seconds": 30},
            timeout=15)
        print(f"  status: {r.status_code}")
        print(f"  body: {r.text[:300]}")
    except Exception as e:
        print(f"  error: {e}")

if __name__ == "__main__":
    tts_model = test_tts()
    test_image()
    test_video()
    test_music()
    print(f"\nWorking TTS model: {tts_model}")
