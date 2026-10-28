"""
Standard ability tag taxonomy for Nautilus agents.

Tags are used to match tasks to capable agents.
OpenClaw agents should register with these standardized tags.

Integration with academic_tasks.py:
  - Call get_preferred_tags_for_task(task_type) to get required tags for a task.
  - Call agent_matches_task(agent.specialties_list, task_type) to check compatibility.
  - In dispatch logic: prefer matched agents, fallback to any alive agent.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 20 standard ability tags
# ---------------------------------------------------------------------------
ABILITY_TAGS: dict[str, str] = {
    # Scientific Computing (matches academic task types)
    "physics-simulation": "Physics simulation and modeling (ODE/PDE/FEM)",
    "ml-training": "Machine learning model training and evaluation",
    "statistical-analysis": "Statistical analysis and hypothesis testing",
    "curve-fitting": "Numerical curve fitting and regression",
    "monte-carlo": "Monte Carlo simulation and stochastic methods",
    "data-visualization": "Scientific data visualization",
    "numerical-computation": "General numerical computation",

    # Research & Knowledge
    "research-synthesis": "Literature review and research synthesis",
    "technical-writing": "Technical documentation and report writing",
    "data-collection": "Web scraping and data collection",

    # AI/Agent Specific
    "code-generation": "Code generation and debugging",
    "reasoning": "Multi-step reasoning and problem decomposition",
    "tool-use": "External API and tool integration",
    "multimodal": "Image/audio/video processing",

    # Domain Knowledge
    "materials-science": "Materials science and constitutive modeling",
    "geotechnical": "Geotechnical and THMC coupling simulation",
    "finance": "Financial analysis and quantitative modeling",
    "biology": "Bioinformatics and computational biology",
    "chemistry": "Computational chemistry and molecular modeling",
    "engineering": "General engineering simulation and CAD",

    # Multimodal capabilities
    "image_analysis": "Analyze images using Gemini Vision — object detection, text extraction, scene description",
    "audio_transcription": "Transcribe and summarize audio files — meetings, podcasts, interviews",
    "tts_generation": "Convert text reports to natural speech audio via MiniMax TTS",
    "document_analysis": "Analyze PDF/image documents — OCR, data extraction, summarization",
    "vision": "General computer vision capabilities",
    "speech": "Speech processing — recognition and synthesis",
    "ocr": "Optical character recognition from images and documents",
    "image_generation": "Generate images from text prompts using Imagen 4",
}

# ---------------------------------------------------------------------------
# Task type → required ability tags mapping
# ---------------------------------------------------------------------------
TASK_TYPE_TO_TAGS: dict[str, list[str]] = {
    "physics_simulation": ["physics-simulation", "numerical-computation"],
    "pde_simulation": ["physics-simulation", "numerical-computation"],
    "ode_simulation": ["physics-simulation", "numerical-computation"],
    "ml_training": ["ml-training"],
    "monte_carlo": ["monte-carlo", "numerical-computation"],
    "statistical_analysis": ["statistical-analysis"],
    "curve_fitting": ["curve-fitting", "numerical-computation"],
    "data_visualization": ["data-visualization"],
    "general_computation": ["numerical-computation"],
    "jc_constitutive": ["materials-science", "physics-simulation"],
    "thmc_coupling": ["geotechnical", "physics-simulation"],
    "research_synthesis": ["research-synthesis", "reasoning"],
    "image_analysis": ["image_analysis", "vision"],
    "audio_transcription": ["audio_transcription", "speech"],
    "tts_generation": ["tts_generation", "speech"],
    "document_analysis": ["document_analysis", "vision", "ocr"],
    "image_generation": ["image_generation", "multimodal"],
}


def get_preferred_tags_for_task(task_type: str) -> list[str]:
    """Return preferred ability tags for a given task type.

    Falls back to ["numerical-computation"] for unknown task types.
    """
    return TASK_TYPE_TO_TAGS.get(task_type, ["numerical-computation"])


def agent_matches_task(agent_specialties: list[str], task_type: str) -> bool:
    """Check if an agent's specialties include at least one tag preferred by the task.

    Args:
        agent_specialties: List of ability tag strings from the agent's specialties field.
        task_type: Academic task type key (e.g. "physics_simulation").

    Returns:
        True if there is any overlap, or if agent_specialties is empty (general-purpose agent).
    """
    if not agent_specialties:
        return True  # No specialties = general purpose, accepts all tasks
    preferred = set(get_preferred_tags_for_task(task_type))
    agent_tags = {t.lower().strip() for t in agent_specialties}
    return bool(preferred & agent_tags)


def normalize_specialties(raw_tags: list[str]) -> list[str]:
    """Normalize agent specialties to standard ability tags where possible.

    Unknown tags are kept as-is (not rejected) with a debug log.
    Deduplicates while preserving order.

    Example:
        normalize_specialties(["physics", "ML", "unknown-tag"])
        -> ["physics-simulation", "ml-training", "unknown-tag"]
    """
    import logging

    if not raw_tags:
        return []

    _logger = logging.getLogger(__name__)
    standard_tags = set(ABILITY_TAGS.keys())
    normalized: list[str] = []

    for tag in raw_tags:
        tag_lower = tag.lower().strip()
        if not tag_lower:
            continue

        # Exact match
        if tag_lower in standard_tags:
            normalized.append(tag_lower)
            continue

        # Fuzzy match: tag is substring of a standard tag, or vice versa
        matched: str | None = None
        for std_tag in standard_tags:
            if tag_lower in std_tag or std_tag in tag_lower:
                matched = std_tag
                break

        if matched:
            normalized.append(matched)
        else:
            _logger.debug(
                "Unknown ability tag '%s', keeping as-is (known tags: %s ...)",
                tag,
                list(standard_tags)[:5],
            )
            normalized.append(tag_lower)

    # Deduplicate while preserving order
    return list(dict.fromkeys(normalized))
