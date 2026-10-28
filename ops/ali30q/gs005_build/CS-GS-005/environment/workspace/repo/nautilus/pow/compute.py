"""
Proof-of-Work (PoW) computation module for Nautilus.

Implements SHA-256 based PoW computation similar to Bitcoin.
"""

import hashlib
import time
from typing import Tuple, Optional


def compute_pow(result: bytes, difficulty: int, max_iterations: int = 10**9) -> Tuple[int, str]:
    """
    Compute PoW proof by finding a nonce that satisfies difficulty requirement.

    Algorithm:
    1. Start with nonce = 0
    2. Compute hash = SHA256(result || nonce)
    3. If hash < target, return (nonce, hash)
    4. Otherwise, increment nonce and repeat

    Args:
        result: Task result bytes
        difficulty: Number of leading zero bits required (e.g., 20 means 20 leading zeros)
        max_iterations: Maximum iterations to prevent infinite loop

    Returns:
        Tuple of (nonce, pow_hash_hex)

    Raises:
        RuntimeError: If max iterations exceeded

    Example:
        >>> result = b"Task completed successfully"
        >>> nonce, pow_hash = compute_pow(result, difficulty=16)
        >>> print(f"Found nonce: {nonce}, hash: {pow_hash}")
    """
    # Calculate target value (2^(256 - difficulty))
    target = 2 ** (256 - difficulty)
    nonce = 0

    while nonce < max_iterations:
        # Concatenate result and nonce
        data = result + nonce.to_bytes(8, 'big')

        # Compute SHA-256 hash
        pow_hash = hashlib.sha256(data).hexdigest()

        # Check if hash meets difficulty requirement
        if int(pow_hash, 16) < target:
            return nonce, pow_hash

        nonce += 1

    raise RuntimeError(f"PoW computation exceeded maximum iterations ({max_iterations})")


def compute_pow_with_stats(
    result: bytes,
    difficulty: int,
    max_iterations: int = 10**9
) -> dict:
    """
    Compute PoW with performance statistics.

    Args:
        result: Task result bytes
        difficulty: Number of leading zero bits required
        max_iterations: Maximum iterations

    Returns:
        Dictionary with nonce, hash, time_elapsed, iterations

    Example:
        >>> result = b"Task completed"
        >>> stats = compute_pow_with_stats(result, difficulty=16)
        >>> print(f"Time: {stats['time_elapsed']:.2f}s, Iterations: {stats['iterations']}")
    """
    start_time = time.time()

    nonce, pow_hash = compute_pow(result, difficulty, max_iterations)

    elapsed_time = time.time() - start_time

    return {
        'nonce': nonce,
        'pow_hash': pow_hash,
        'time_elapsed': elapsed_time,
        'iterations': nonce + 1,
        'hash_rate': (nonce + 1) / elapsed_time if elapsed_time > 0 else 0
    }


def estimate_computation_time(difficulty: int, hash_rate: float = 1000000) -> float:
    """
    Estimate PoW computation time based on difficulty and hash rate.

    Args:
        difficulty: Number of leading zero bits
        hash_rate: Estimated hash rate (hashes per second)

    Returns:
        Estimated time in seconds

    Example:
        >>> time_estimate = estimate_computation_time(difficulty=20, hash_rate=1000000)
        >>> print(f"Estimated time: {time_estimate:.2f} seconds")
    """
    # Expected number of iterations = 2^difficulty
    expected_iterations = 2 ** difficulty

    # Estimated time = iterations / hash_rate
    estimated_time = expected_iterations / hash_rate

    return estimated_time
