@echo off
REM 测试覆盖率提升验证脚本 (Windows版本)
REM 运行新增的测试并生成覆盖率报告

echo ==========================================
echo 测试覆盖率提升验证脚本
echo ==========================================
echo.

REM 检查pytest是否安装
pytest --version >nul 2>&1
if errorlevel 1 (
    echo 错误: pytest未安装
    echo 请运行: pip install pytest pytest-cov
    exit /b 1
)

echo 步骤 1: 运行新增的认证API测试
pytest tests/test_api_auth_extended.py -v --tb=short
set AUTH_RESULT=%ERRORLEVEL%

echo.
echo 步骤 2: 运行新增的奖励API测试
pytest tests/test_api_rewards_extended.py -v --tb=short
set REWARDS_RESULT=%ERRORLEVEL%

echo.
echo 步骤 3: 运行新增的任务API测试
pytest tests/test_api_tasks_extended.py -v --tb=short
set TASKS_RESULT=%ERRORLEVEL%

echo.
echo 步骤 4: 运行新增的区块链服务Mock测试
pytest tests/test_blockchain_service_mock.py -v --tb=short
set BLOCKCHAIN_RESULT=%ERRORLEVEL%

echo.
echo ==========================================
echo 测试结果汇总
echo ==========================================

if %AUTH_RESULT%==0 (
    echo [OK] 认证API测试: 通过
) else (
    echo [FAIL] 认证API测试: 失败
)

if %REWARDS_RESULT%==0 (
    echo [OK] 奖励API测试: 通过
) else (
    echo [FAIL] 奖励API测试: 失败
)

if %TASKS_RESULT%==0 (
    echo [OK] 任务API测试: 通过
) else (
    echo [FAIL] 任务API测试: 失败
)

if %BLOCKCHAIN_RESULT%==0 (
    echo [OK] 区块链服务测试: 通过
) else (
    echo [FAIL] 区块链服务测试: 失败
)

echo.
echo 步骤 5: 生成覆盖率报告
pytest tests/test_api_auth_extended.py tests/test_api_rewards_extended.py tests/test_api_tasks_extended.py tests/test_blockchain_service_mock.py --cov=api --cov=blockchain --cov-report=term-missing --cov-report=html -v

echo.
echo ==========================================
echo 覆盖率报告已生成
echo ==========================================
echo HTML报告位置: htmlcov\index.html
echo.
echo 查看报告: start htmlcov\index.html
echo.

REM 计算总体结果
set /a TOTAL_RESULT=%AUTH_RESULT%+%REWARDS_RESULT%+%TASKS_RESULT%+%BLOCKCHAIN_RESULT%

if %TOTAL_RESULT%==0 (
    echo ==========================================
    echo 所有新增测试通过！
    echo ==========================================
    exit /b 0
) else (
    echo ==========================================
    echo 部分测试失败，请检查错误信息
    echo ==========================================
    exit /b 1
)
