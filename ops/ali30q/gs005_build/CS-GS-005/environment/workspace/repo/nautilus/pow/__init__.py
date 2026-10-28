"""
Proof-of-Work (PoW) module for Nautilus.

Implements:
- PoW computation (SHA-256 based)
- PoW verification
- Dynamic difficulty adjustment
- Smart contract integration
"""

from .compute import compute_pow, compute_pow_with_stats, estimate_computation_time
from .verify import verify_pow, verify_pow_detailed, batch_verify_pow, count_leading_zeros
from .difficulty import (
    adjust_difficulty,
    adjust_difficulty_batch,
    calculate_target_from_difficulty,
    calculate_difficulty_from_target,
    DifficultyAdjuster
)

__all__ = [
    'compute_pow',
    'compute_pow_with_stats',
    'estimate_computation_time',
    'verify_pow',
    'verify_pow_detailed',
    'batch_verify_pow',
    'count_leading_zeros',
    'adjust_difficulty',
    'adjust_difficulty_batch',
    'calculate_target_from_difficulty',
    'calculate_difficulty_from_target',
    'DifficultyAdjuster'
]
