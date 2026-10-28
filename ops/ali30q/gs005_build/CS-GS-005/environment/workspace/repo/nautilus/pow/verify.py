"""
Proof-of-Work (PoW) verification module for Nautilus.

Verifies PoW proofs submitted by agents.
"""

import hashlib
from typing import Optional


def verify_pow(
    result: bytes,
    nonce: int,
    expected_hash: str,
    difficulty: int
) -> bool:
    """
    Verify a PoW proof.

    Verification steps:
    1. Recompute hash = SHA256(result || nonce)
    2. Check if computed hash matches expected hash
    3. Check if hash meets difficulty requirement

    Args:
        result: Task result bytes
        nonce: PoW nonce
        expected_hash: Expected PoW hash (hex string)
        difficulty: Number of leading zero bits required

    Returns:
        True if proof is valid, False otherwise

    Example:
        >>> result = b"Task completed"
        >>> nonce = 12345
        >>> pow_hash = "00000abcdef..."
        >>> is_valid = verify_pow(result, nonce, pow_hash, difficulty=20)
    """
    # Recompute hash
    data = result + nonce.to_bytes(8, 'big')
    computed_hash = hashlib.sha256(data).hexdigest()

    # Check if hash matches
    if computed_hash != expected_hash:
        return False

    # Check if hash meets difficulty requirement
    target = 2 ** (256 - difficulty)
    if int(computed_hash, 16) >= target:
        return False

    return True


def verify_pow_detailed(
    result: bytes,
    nonce: int,
    expected_hash: str,
    difficulty: int
) -> dict:
    """
    Verify PoW proof with detailed results.

    Args:
        result: Task result bytes
        nonce: PoW nonce
        expected_hash: Expected PoW hash
        difficulty: Number of leading zero bits required

    Returns:
        Dictionary with verification results and details

    Example:
        >>> details = verify_pow_detailed(result, nonce, pow_hash, difficulty=20)
        >>> print(f"Valid: {details['valid']}, Reason: {details['reason']}")
    """
    # Recompute hash
    data = result + nonce.to_bytes(8, 'big')
    computed_hash = hashlib.sha256(data).hexdigest()

    # Initialize result
    result_dict = {
        'valid': False,
        'computed_hash': computed_hash,
        'expected_hash': expected_hash,
        'hash_matches': False,
        'difficulty_met': False,
        'reason': ''
    }

    # Check hash match
    if computed_hash != expected_hash:
        result_dict['reason'] = 'Hash mismatch'
        return result_dict

    result_dict['hash_matches'] = True

    # Check difficulty
    target = 2 ** (256 - difficulty)
    hash_value = int(computed_hash, 16)

    if hash_value >= target:
        result_dict['reason'] = f'Difficulty not met (hash: {hash_value}, target: {target})'
        return result_dict

    result_dict['difficulty_met'] = True
    result_dict['valid'] = True
    result_dict['reason'] = 'Valid proof'

    return result_dict


def batch_verify_pow(proofs: list) -> dict:
    """
    Verify multiple PoW proofs in batch.

    Args:
        proofs: List of proof dictionaries with keys:
                'result', 'nonce', 'expected_hash', 'difficulty'

    Returns:
        Dictionary with verification statistics

    Example:
        >>> proofs = [
        ...     {'result': b"Task 1", 'nonce': 123, 'expected_hash': "...", 'difficulty': 20},
        ...     {'result': b"Task 2", 'nonce': 456, 'expected_hash': "...", 'difficulty': 20}
        ... ]
        >>> stats = batch_verify_pow(proofs)
        >>> print(f"Valid: {stats['valid_count']}/{stats['total_count']}")
    """
    total_count = len(proofs)
    valid_count = 0
    invalid_proofs = []

    for i, proof in enumerate(proofs):
        is_valid = verify_pow(
            proof['result'],
            proof['nonce'],
            proof['expected_hash'],
            proof['difficulty']
        )

        if is_valid:
            valid_count += 1
        else:
            invalid_proofs.append({
                'index': i,
                'proof': proof
            })

    return {
        'total_count': total_count,
        'valid_count': valid_count,
        'invalid_count': total_count - valid_count,
        'success_rate': valid_count / total_count if total_count > 0 else 0,
        'invalid_proofs': invalid_proofs
    }


def count_leading_zeros(hash_hex: str) -> int:
    """
    Count leading zero bits in a hash.

    Args:
        hash_hex: Hash in hexadecimal format

    Returns:
        Number of leading zero bits

    Example:
        >>> hash_hex = "0000abcdef..."
        >>> zeros = count_leading_zeros(hash_hex)
        >>> print(f"Leading zeros: {zeros}")
    """
    # Convert hex to binary
    hash_int = int(hash_hex, 16)
    hash_bin = bin(hash_int)[2:].zfill(256)  # 256-bit hash

    # Count leading zeros
    leading_zeros = 0
    for bit in hash_bin:
        if bit == '0':
            leading_zeros += 1
        else:
            break

    return leading_zeros
