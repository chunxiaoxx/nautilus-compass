"""
Unit tests for PoW (Proof-of-Work) module.

Tests:
- PoW computation (SHA-256)
- PoW verification
- Dynamic difficulty adjustment
- Performance benchmarks
"""

import pytest
import time
from nautilus.pow import (
    compute_pow,
    compute_pow_with_stats,
    estimate_computation_time,
    verify_pow,
    verify_pow_detailed,
    batch_verify_pow,
    count_leading_zeros,
    adjust_difficulty,
    adjust_difficulty_batch,
    calculate_target_from_difficulty,
    calculate_difficulty_from_target,
    DifficultyAdjuster
)


class TestPoWComputation:
    """Test PoW computation."""

    def test_compute_pow_basic(self):
        """Test basic PoW computation."""
        result = b"Task completed successfully"
        difficulty = 12  # Easy difficulty for fast testing

        nonce, pow_hash = compute_pow(result, difficulty)

        # Verify nonce is non-negative
        assert nonce >= 0

        # Verify hash is valid hex string
        assert len(pow_hash) == 64
        assert all(c in '0123456789abcdef' for c in pow_hash)

        # Verify hash meets difficulty
        target = 2 ** (256 - difficulty)
        assert int(pow_hash, 16) < target

    def test_compute_pow_with_stats(self):
        """Test PoW computation with statistics."""
        result = b"Test task"
        difficulty = 12

        stats = compute_pow_with_stats(result, difficulty)

        assert 'nonce' in stats
        assert 'pow_hash' in stats
        assert 'time_elapsed' in stats
        assert 'iterations' in stats
        assert 'hash_rate' in stats

        assert stats['nonce'] >= 0
        assert stats['time_elapsed'] > 0
        assert stats['iterations'] > 0
        assert stats['hash_rate'] > 0

    def test_compute_pow_different_results_different_nonces(self):
        """Test that different results produce different nonces."""
        result1 = b"Task 1"
        result2 = b"Task 2"
        difficulty = 12

        nonce1, hash1 = compute_pow(result1, difficulty)
        nonce2, hash2 = compute_pow(result2, difficulty)

        # Different results should produce different hashes
        assert hash1 != hash2

    def test_estimate_computation_time(self):
        """Test computation time estimation."""
        difficulty = 16
        hash_rate = 1000000  # 1M hashes/sec

        estimated_time = estimate_computation_time(difficulty, hash_rate)

        # Should return a positive number
        assert estimated_time > 0

        # Higher difficulty should take longer
        estimated_time_harder = estimate_computation_time(difficulty + 4, hash_rate)
        assert estimated_time_harder > estimated_time


class TestPoWVerification:
    """Test PoW verification."""

    def test_verify_pow_valid(self):
        """Test verification of valid PoW."""
        result = b"Task completed"
        difficulty = 12

        nonce, pow_hash = compute_pow(result, difficulty)

        # Verify should pass
        assert verify_pow(result, nonce, pow_hash, difficulty) is True

    def test_verify_pow_invalid_nonce(self):
        """Test verification fails with wrong nonce."""
        result = b"Task completed"
        difficulty = 12

        nonce, pow_hash = compute_pow(result, difficulty)

        # Wrong nonce should fail
        assert verify_pow(result, nonce + 1, pow_hash, difficulty) is False

    def test_verify_pow_invalid_hash(self):
        """Test verification fails with wrong hash."""
        result = b"Task completed"
        difficulty = 12

        nonce, pow_hash = compute_pow(result, difficulty)

        # Wrong hash should fail
        wrong_hash = "0" * 64
        assert verify_pow(result, nonce, wrong_hash, difficulty) is False

    def test_verify_pow_detailed(self):
        """Test detailed verification."""
        result = b"Task completed"
        difficulty = 12

        nonce, pow_hash = compute_pow(result, difficulty)

        details = verify_pow_detailed(result, nonce, pow_hash, difficulty)

        assert details['valid'] is True
        assert details['hash_matches'] is True
        assert details['difficulty_met'] is True
        assert details['reason'] == 'Valid proof'

    def test_verify_pow_detailed_invalid(self):
        """Test detailed verification with invalid proof."""
        result = b"Task completed"
        difficulty = 12

        nonce, pow_hash = compute_pow(result, difficulty)

        # Use wrong nonce
        details = verify_pow_detailed(result, nonce + 1, pow_hash, difficulty)

        assert details['valid'] is False
        assert details['hash_matches'] is False
        assert 'mismatch' in details['reason'].lower()

    def test_batch_verify_pow(self):
        """Test batch verification."""
        proofs = []

        for i in range(5):
            result = f"Task {i}".encode()
            difficulty = 12
            nonce, pow_hash = compute_pow(result, difficulty)

            proofs.append({
                'result': result,
                'nonce': nonce,
                'expected_hash': pow_hash,
                'difficulty': difficulty
            })

        stats = batch_verify_pow(proofs)

        assert stats['total_count'] == 5
        assert stats['valid_count'] == 5
        assert stats['invalid_count'] == 0
        assert stats['success_rate'] == 1.0

    def test_count_leading_zeros(self):
        """Test counting leading zeros in hash."""
        # Hash with 16 leading zero bits (4 hex zeros)
        hash_hex = "0000" + "f" * 60

        zeros = count_leading_zeros(hash_hex)

        # Should have at least 16 leading zeros
        assert zeros >= 16


class TestDifficultyAdjustment:
    """Test difficulty adjustment."""

    def test_adjust_difficulty_too_slow(self):
        """Test difficulty decreases when computation is too slow."""
        current_difficulty = 20
        target_time = 20.0
        actual_time = 40.0  # 2x slower

        new_difficulty = adjust_difficulty(current_difficulty, target_time, actual_time)

        # Should decrease difficulty (easier)
        assert new_difficulty < current_difficulty

    def test_adjust_difficulty_too_fast(self):
        """Test difficulty increases when computation is too fast."""
        current_difficulty = 20
        target_time = 20.0
        actual_time = 5.0  # 4x faster

        new_difficulty = adjust_difficulty(current_difficulty, target_time, actual_time)

        # Should increase difficulty (harder)
        assert new_difficulty > current_difficulty

    def test_adjust_difficulty_within_range(self):
        """Test difficulty stays same when within acceptable range."""
        current_difficulty = 20
        target_time = 20.0
        actual_time = 22.0  # Close to target

        new_difficulty = adjust_difficulty(current_difficulty, target_time, actual_time)

        # Should keep same difficulty
        assert new_difficulty == current_difficulty

    def test_calculate_target_from_difficulty(self):
        """Test target calculation from difficulty."""
        difficulty = 20
        target = calculate_target_from_difficulty(difficulty)

        # Target should be 2^(256-20) = 2^236
        assert target == 2 ** 236


class TestPoWIntegration:
    """Integration tests for complete PoW flow."""

    def test_complete_pow_flow(self):
        """Test complete PoW computation and verification flow."""
        result = b"Complete task result"
        difficulty = 12

        # Compute PoW
        nonce, pow_hash = compute_pow(result, difficulty)

        # Verify PoW
        is_valid = verify_pow(result, nonce, pow_hash, difficulty)

        assert is_valid is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
