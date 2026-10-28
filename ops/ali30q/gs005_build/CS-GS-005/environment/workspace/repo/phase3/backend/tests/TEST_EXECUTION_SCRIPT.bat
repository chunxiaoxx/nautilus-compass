@echo off
REM Test Execution Script for Nautilus Phase 3 Backend (Windows)
REM Usage: tests\TEST_EXECUTION_SCRIPT.bat [quick|full|coverage|smoke]

setlocal

cd /d "%~dp0\.."

echo ==========================================
echo Nautilus Phase 3 - Test Execution
echo ==========================================
echo Working Directory: %CD%
echo.

set TEST_MODE=%1
if "%TEST_MODE%"=="" set TEST_MODE=quick

if "%TEST_MODE%"=="smoke" (
    echo Running SMOKE TESTS (fastest validation)...
    echo.
    python tests\run_smoke_test.py
    goto :end
)

if "%TEST_MODE%"=="quick" (
    echo Running QUICK TESTS (core functionality)...
    echo.
    python tests\run_quick_test.py
    goto :end
)

if "%TEST_MODE%"=="full" (
    echo Running FULL TEST SUITE (with coverage)...
    echo.
    python tests\run_test_suite.py
    goto :end
)

if "%TEST_MODE%"=="coverage" (
    echo Running ALL TESTS with COVERAGE ANALYSIS...
    echo.
    pytest tests\ -v --cov=. --cov-report=html --cov-report=term-missing --cov-report=json --tb=short
    echo.
    echo Coverage report generated: htmlcov\index.html
    goto :end
)

if "%TEST_MODE%"=="blockchain" (
    echo Running BLOCKCHAIN TESTS...
    echo.
    pytest tests\test_blockchain_integration.py tests\test_wallet_auth.py tests\test_wallet_auth_e2e.py -v --tb=short
    goto :end
)

if "%TEST_MODE%"=="evomap" (
    echo Running EVOMAP TESTS (Week 5)...
    echo.
    pytest tests\test_agent_evolution.py tests\test_evomap_integration.py tests\test_enhanced_reflection.py tests\test_knowledge_extraction.py -v --tb=short
    goto :end
)

if "%TEST_MODE%"=="week4" (
    echo Running WEEK 4 INTEGRATION TESTS...
    echo.
    pytest tests\test_week4_integration.py tests\test_knowledge_value_integration.py tests\test_roi_enhancement.py -v --tb=short
    goto :end
)

if "%TEST_MODE%"=="week5" (
    echo Running WEEK 5 TESTS...
    echo.
    pytest tests\test_week5_performance.py tests\test_capability_capsule.py tests\test_capability_transfer.py tests\test_knowledge_emergence.py -v --tb=short
    goto :end
)

if "%TEST_MODE%"=="performance" (
    echo Running PERFORMANCE TESTS...
    echo.
    pytest tests\test_performance_suite.py tests\test_cache_performance.py tests\test_async_optimization.py -v --tb=short
    goto :end
)

if "%TEST_MODE%"=="security" (
    echo Running SECURITY TESTS...
    echo.
    pytest tests\test_security_suite.py tests\security\test_security.py tests\test_anti_cheat.py -v --tb=short
    goto :end
)

echo Unknown test mode: %TEST_MODE%
echo.
echo Usage: tests\TEST_EXECUTION_SCRIPT.bat [MODE]
echo.
echo Available modes:
echo   smoke       - Fastest validation (2 min)
echo   quick       - Core functionality (5-10 min)
echo   full        - Full test suite with coverage (15-20 min)
echo   coverage    - All tests with detailed coverage (45-60 min)
echo   blockchain  - Blockchain integration tests
echo   evomap      - EvoMap/Week 5 tests
echo   week4       - Week 4 integration tests
echo   week5       - Week 5 specific tests
echo   performance - Performance tests
echo   security    - Security tests
exit /b 1

:end
echo.
echo ==========================================
echo Test execution completed!
echo ==========================================
endlocal
