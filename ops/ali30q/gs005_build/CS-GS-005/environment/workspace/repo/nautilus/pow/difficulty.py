"""
Dynamic difficulty adjustment for PoW.

Adjusts difficulty based on actual computation time to maintain target time.
"""

from typing import List, Optional


def adjust_difficulty(
    current_difficulty: int,
    target_time: float,
    actual_time: float,
    min_difficulty: int = 10,
    max_difficulty: int = 30
) -> int:
    """
    Adjust PoW difficulty based on actual computation time.

    Algorithm:
    - If actual_time > target_time * 1.5: decrease difficulty (easier)
    - If actual_time < target_time * 0.5: increase difficulty (harder)
    - Otherwise: keep current difficulty

    Args:
        current_difficulty: Current difficulty level
        target_time: Target computation time in seconds (e.g., 20)
        actual_time: Actual computation time in seconds
        min_difficulty: Minimum difficulty (default: 10)
        max_difficulty: Maximum difficulty (default: 30)

    Returns:
        New difficulty level

    Example:
        >>> new_diff = adjust_difficulty(20, target_time=20, actual_time=40)
        >>> print(f"Difficulty adjusted: 20 -> {new_diff}")
    """
    ratio = actual_time / target_time

    if ratio > 1.5:  # Too slow, decrease difficulty
        new_difficulty = max(min_difficulty, current_difficulty - 1)
    elif ratio < 0.5:  # Too fast, increase difficulty
        new_difficulty = min(max_difficulty, current_difficulty + 1)
    else:  # Within acceptable range
        new_difficulty = current_difficulty

    return new_difficulty


def adjust_difficulty_batch(
    current_difficulty: int,
    target_time: float,
    actual_times: List[float],
    min_difficulty: int = 10,
    max_difficulty: int = 30
) -> int:
    """
    Adjust difficulty based on multiple computation times (batch).

    Uses average of actual times for more stable adjustment.

    Args:
        current_difficulty: Current difficulty level
        target_time: Target computation time in seconds
        actual_times: List of actual computation times
        min_difficulty: Minimum difficulty
        max_difficulty: Maximum difficulty

    Returns:
        New difficulty level

    Example:
        >>> times = [18.5, 22.3, 19.8, 21.1]
        >>> new_diff = adjust_difficulty_batch(20, target_time=20, actual_times=times)
    """
    if not actual_times:
        return current_difficulty

    # Calculate average time
    avg_time = sum(actual_times) / len(actual_times)

    # Adjust based on average
    return adjust_difficulty(
        current_difficulty,
        target_time,
        avg_time,
        min_difficulty,
        max_difficulty
    )


def calculate_target_from_difficulty(difficulty: int) -> int:
    """
    Calculate target value from difficulty.

    Target = 2^(256 - difficulty)

    Args:
        difficulty: Number of leading zero bits

    Returns:
        Target value as integer

    Example:
        >>> target = calculate_target_from_difficulty(20)
        >>> print(f"Target: {target}")
    """
    return 2 ** (256 - difficulty)


def calculate_difficulty_from_target(target: int) -> int:
    """
    Calculate difficulty from target value.

    Difficulty = 256 - log2(target)

    Args:
        target: Target value

    Returns:
        Difficulty (number of leading zero bits)

    Example:
        >>> difficulty = calculate_difficulty_from_target(2**236)
        >>> print(f"Difficulty: {difficulty}")
    """
    import math
    return 256 - int(math.log2(target))


class DifficultyAdjuster:
    """
    Manages difficulty adjustment with history tracking.
    """

    def __init__(
        self,
        initial_difficulty: int = 16,
        target_time: float = 20.0,
        adjustment_interval: int = 100,
        min_difficulty: int = 10,
        max_difficulty: int = 30
    ):
        """
        Initialize difficulty adjuster.

        Args:
            initial_difficulty: Starting difficulty
            target_time: Target computation time in seconds
            adjustment_interval: Adjust after N proofs
            min_difficulty: Minimum difficulty
            max_difficulty: Maximum difficulty
        """
        self.current_difficulty = initial_difficulty
        self.target_time = target_time
        self.adjustment_interval = adjustment_interval
        self.min_difficulty = min_difficulty
        self.max_difficulty = max_difficulty

        self.computation_times = []
        self.difficulty_history = [initial_difficulty]
        self.proof_count = 0

    def record_computation(self, time_elapsed: float):
        """
        Record a computation time.

        Args:
            time_elapsed: Time taken to compute PoW
        """
        self.computation_times.append(time_elapsed)
        self.proof_count += 1

        # Adjust difficulty if interval reached
        if self.proof_count % self.adjustment_interval == 0:
            self._adjust()

    def _adjust(self):
        """Perform difficulty adjustment based on recorded times."""
        if not self.computation_times:
            return

        # Calculate average time for last interval
        recent_times = self.computation_times[-self.adjustment_interval:]
        avg_time = sum(recent_times) / len(recent_times)

        # Adjust difficulty
        new_difficulty = adjust_difficulty(
            self.current_difficulty,
            self.target_time,
            avg_time,
            self.min_difficulty,
            self.max_difficulty
        )

        if new_difficulty != self.current_difficulty:
            self.current_difficulty = new_difficulty
            self.difficulty_history.append(new_difficulty)

    def get_current_difficulty(self) -> int:
        """Get current difficulty level."""
        return self.current_difficulty

    def get_statistics(self) -> dict:
        """
        Get difficulty adjustment statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.computation_times:
            return {
                'current_difficulty': self.current_difficulty,
                'proof_count': self.proof_count,
                'avg_time': 0,
                'target_time': self.target_time
            }

        return {
            'current_difficulty': self.current_difficulty,
            'proof_count': self.proof_count,
            'avg_time': sum(self.computation_times) / len(self.computation_times),
            'min_time': min(self.computation_times),
            'max_time': max(self.computation_times),
            'target_time': self.target_time,
            'difficulty_history': self.difficulty_history
        }
