"""
Test Suite Runner for Nautilus Phase 3 Backend.

Runs all test suites and generates comprehensive coverage report.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print results."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"{'='*80}\n")

    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0


def main():
    """Run all test suites."""
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    print("Nautilus Phase 3 - Automated Test Suite")
    print("=" * 80)

    # Test suites to run
    test_suites = [
        {
            "name": "API Integration Tests",
            "command": "pytest tests/test_api_integration.py -v --tb=short",
            "critical": True
        },
        {
            "name": "End-to-End Workflow Tests",
            "command": "pytest tests/test_e2e_workflow.py -v --tb=short",
            "critical": True
        },
        {
            "name": "Performance Tests",
            "command": "pytest tests/test_performance_suite.py -v --tb=short",
            "critical": False
        },
        {
            "name": "Security Tests",
            "command": "pytest tests/test_security_suite.py -v --tb=short",
            "critical": True
        },
        {
            "name": "All Tests with Coverage",
            "command": "pytest tests/test_api_integration.py tests/test_e2e_workflow.py tests/test_performance_suite.py tests/test_security_suite.py -v --cov=. --cov-report=html --cov-report=term-missing --cov-report=json",
            "critical": True
        }
    ]

    results = []

    for suite in test_suites:
        success = run_command(suite["command"], suite["name"])
        results.append({
            "name": suite["name"],
            "success": success,
            "critical": suite["critical"]
        })

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")

    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed

    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        critical = " (CRITICAL)" if result["critical"] else ""
        print(f"{status}{critical}: {result['name']}")

    print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}")

    # Check if any critical tests failed
    critical_failures = [r for r in results if not r["success"] and r["critical"]]

    if critical_failures:
        print("\n⚠️  CRITICAL TESTS FAILED!")
        print("The following critical test suites failed:")
        for failure in critical_failures:
            print(f"  - {failure['name']}")
        return 1

    if failed > 0:
        print("\n⚠️  Some non-critical tests failed.")
        return 1

    print("\n✅ ALL TESTS PASSED!")
    print("\nCoverage report generated in: htmlcov/index.html")

    return 0


if __name__ == "__main__":
    sys.exit(main())
