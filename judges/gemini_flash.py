"""v1.7.1+ · Gemini 2.5 Flash judge · opt-in only.

Activates ONLY when COMPASS_USE_GEMINI_FLASH=1 environment variable is set.
Default disabled · preserves "no LLM at ingest" + "完全本地" core constraint
(daemon.py:12-13 verbatim per user 2026-04-28 rule).

Use cases (per paper/SPEC_LONGMEMEVAL_BENCHMARK.md):
  - LongMemEval-S benchmark judge (vs DeepSeek baseline)
  - paper3 cross-LLM ablation (Flash + DeepSeek + MiniMax)

Service account: chunxiao-vm-260414 (project) · us-central1 (location).
SDK: google-genai (already installed per 5/20 verification).

NEVER call from ingest path · NEVER call from default recall · CALL ONLY when
benchmark/paper code explicitly opts in.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

OPT_IN_ENV = "COMPASS_USE_GEMINI_FLASH"
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_PROJECT = "chunxiao-vm-260414"
DEFAULT_LOCATION = "us-central1"
DEFAULT_SA_PATH_HINT = "C:\\Users\\chunx\\Downloads\\chunxiao-vm-260414-de9e73f4697d.json"


def is_enabled() -> bool:
    """Return True iff COMPASS_USE_GEMINI_FLASH env is set to truthy value."""
    val = os.environ.get(OPT_IN_ENV, "").strip().lower()
    return val in ("1", "true", "yes", "on")


def get_credentials_path() -> Optional[str]:
    """Resolve service account JSON path.

    Order:
      1. GOOGLE_APPLICATION_CREDENTIALS env (standard)
      2. COMPASS_GEMINI_SA_PATH env (compass override)
      3. None (caller must handle · auth may use ADC if available)
    """
    p = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if p and Path(p).exists():
        return p
    p = os.environ.get("COMPASS_GEMINI_SA_PATH", "").strip()
    if p and Path(p).exists():
        return p
    return None


class GeminiFlashJudge:
    """Wrapper for google-genai Gemini Flash · benchmark/paper use only.

    Initialization is LAZY · client only created when first generate() called.
    All operations no-op (return None) if not is_enabled().
    """

    def __init__(self, model: str = DEFAULT_MODEL,
                 project: str = DEFAULT_PROJECT,
                 location: str = DEFAULT_LOCATION):
        self.model = model
        self.project = project
        self.location = location
        self._client = None
        self._init_error: Optional[str] = None

    @property
    def enabled(self) -> bool:
        return is_enabled()

    def _lazy_init(self) -> bool:
        """Initialize google-genai client lazily · returns True on success."""
        if self._client is not None:
            return True
        if not self.enabled:
            self._init_error = (
                f"{OPT_IN_ENV} not set · Gemini Flash judge disabled "
                f"(set env to '1' to enable)"
            )
            return False
        try:
            from google import genai  # type: ignore
            # Set ADC if SA path resolvable
            sa_path = get_credentials_path()
            if sa_path and "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_path
            self._client = genai.Client(vertexai=True, project=self.project,
                                         location=self.location)
            return True
        except ImportError as e:
            self._init_error = f"google-genai SDK not installed: {e}"
            return False
        except Exception as e:
            self._init_error = f"client init failed: {e}"
            return False

    def generate(self, prompt: str, max_tokens: int = 800,
                 temperature: float = 0.2) -> Optional[str]:
        """Generate text via Flash · returns None if disabled or any failure."""
        if not self._lazy_init():
            return None
        try:
            resp = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"max_output_tokens": max_tokens, "temperature": temperature},
            )
            text = getattr(resp, "text", None)
            return text.strip() if text else None
        except Exception as e:
            self._init_error = f"generate failed: {e}"
            return None

    def judge(self, question: str, candidate_answer: str,
              reference: Optional[str] = None) -> Optional[dict]:
        """Judge a candidate answer · returns {score, verdict, rationale} or None.

        Convenience wrapper for benchmark eval · structured prompt.
        """
        if not self.enabled:
            return None
        prompt_parts = [
            "You are a strict judge evaluating an AI agent's answer.",
            f"Question: {question}",
            f"Candidate answer: {candidate_answer}",
        ]
        if reference:
            prompt_parts.append(f"Reference answer: {reference}")
        prompt_parts.append(
            "Respond with JSON ONLY: {\"score\": 0-1, \"verdict\": \"correct/partial/wrong\", "
            "\"rationale\": \"...one sentence...\"}"
        )
        result_text = self.generate("\n\n".join(prompt_parts))
        if not result_text:
            return None
        # Try parse JSON · graceful fallback
        import json
        try:
            cleaned = result_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```", 2)[1] if "```" in cleaned[3:] else cleaned[3:]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3].strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            return {"score": None, "verdict": "parse_error", "rationale": result_text[:200]}


def get_default_judge() -> GeminiFlashJudge:
    """Convenience singleton for default config."""
    return GeminiFlashJudge()
