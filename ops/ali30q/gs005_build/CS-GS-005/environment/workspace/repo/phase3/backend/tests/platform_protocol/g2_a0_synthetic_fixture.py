from __future__ import annotations

from dataclasses import dataclass

_FIXTURE_VERSION = "g2-a0-synthetic-repair-v1"
_TARGET_RELATIVE_PATH = "synthetic_target.py"
_SOURCE_BYTES = b"def clamp_score(value):\n    return max(0, value)\n"
_PUBLIC_PROMPT = (
    "Repair clamp_score so every integer result is clamped to 0 through 100, "
    "and reject non-integer input with TypeError. Return only the approved JSON."
)
_PUBLIC_EXAMPLE = "clamp_score(120) == 100"


@dataclass(frozen=True, slots=True)
class SyntheticRepairFixtureV1:
    fixture_version: str
    target_relative_path: str
    source_bytes: bytes
    public_prompt: str
    public_example: str
    public_case_count: int
    hidden_case_count: int

    def __post_init__(self) -> None:
        if self != self.default():
            raise ValueError("invalid_fixture")

    @classmethod
    def default(cls) -> SyntheticRepairFixtureV1:
        return cls.__new_default()

    @classmethod
    def __new_default(cls) -> SyntheticRepairFixtureV1:
        instance = object.__new__(cls)
        object.__setattr__(instance, "fixture_version", _FIXTURE_VERSION)
        object.__setattr__(instance, "target_relative_path", _TARGET_RELATIVE_PATH)
        object.__setattr__(instance, "source_bytes", _SOURCE_BYTES)
        object.__setattr__(instance, "public_prompt", _PUBLIC_PROMPT)
        object.__setattr__(instance, "public_example", _PUBLIC_EXAMPLE)
        object.__setattr__(instance, "public_case_count", 3)
        object.__setattr__(instance, "hidden_case_count", 10)
        return instance
