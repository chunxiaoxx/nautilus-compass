#!/usr/bin/env python3
"""
Quick verification script for security fixes.
Run this to verify all security fixes are properly implemented.
"""

import sys
import os

def check_file_contains(filepath, search_strings, description):
    """Check if file contains all required strings."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        missing = []
        for search_str in search_strings:
            if search_str not in content:
                missing.append(search_str)

        if missing:
            print(f"❌ {description}")
            for m in missing:
                print(f"   Missing: {m}")
            return False
        else:
            print(f"✅ {description}")
            return True
    except FileNotFoundError:
        print(f"❌ {description} - File not found: {filepath}")
        return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Security Fixes Verification")
    print("=" * 60)
    print()

    checks = []

    # C1: Check asteval is used instead of eval()
    checks.append(check_file_contains(
        "agent_engine/executors/compute_executor.py",
        ["from asteval import Interpreter", "aeval = Interpreter()", "aeval(expression)"],
        "C1: asteval replaces eval()"
    ))

    # H1: Check rate limiting on agent registration
    checks.append(check_file_contains(
        "api/agents.py",
        ["from slowapi import Limiter", '@limiter.limit("3/hour")'],
        "H1: Rate limiting on agent registration"
    ))

    # H2: Check eth_account for wallet generation
    checks.append(check_file_contains(
        "api/agents.py",
        ["from eth_account import Account", "account = Account.create()", "return account.address"],
        "H2: Secure wallet generation with eth_account"
    ))

    # H3: Check OAuth state validation with Redis
    checks.append(check_file_contains(
        "api/auth.py",
        ["import redis", "redis_client.setex(f\"oauth_state:{state}\"", "redis_client.get(f\"oauth_state:{state}\")"],
        "H3: OAuth state validation with Redis"
    ))

    # H4: Check HIBP integration
    checks.append(check_file_contains(
        "api/auth.py",
        ["import hashlib", "api.pwnedpasswords.com", "This password has been exposed"],
        "H4: Have I Been Pwned integration"
    ))

    # Check requirements.txt updated
    checks.append(check_file_contains(
        "requirements.txt",
        ["asteval>=0.9.31", "eth-account>=0.10.0"],
        "Dependencies: asteval and eth-account added"
    ))

    # Check test file exists
    checks.append(check_file_contains(
        "tests/test_security_fixes.py",
        ["test_compute_executor_blocks_code_injection", "test_wallet_generation_uses_eth_account", "test_oauth_callback_validates_state"],
        "Tests: Security test suite created"
    ))

    # Check documentation exists
    checks.append(check_file_contains(
        "SECURITY_FIXES.md",
        ["C1: eval() Code Injection", "H1: Agent Registration", "H2: Insecure Wallet", "H3: OAuth State", "H4: Weak Password"],
        "Documentation: SECURITY_FIXES.md created"
    ))

    print()
    print("=" * 60)

    passed = sum(checks)
    total = len(checks)

    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("✅ All security fixes verified successfully!")
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run tests: pytest tests/test_security_fixes.py -v")
        print("3. Commit changes: git add . && git commit -m 'fix: address P0 security vulnerabilities'")
        return 0
    else:
        print("❌ Some security fixes are missing or incomplete")
        print("Please review the failed checks above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
