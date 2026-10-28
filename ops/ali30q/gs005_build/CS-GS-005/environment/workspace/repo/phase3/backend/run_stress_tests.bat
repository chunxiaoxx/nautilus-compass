@echo off
REM Nexus Protocol 压力测试启动脚本 (Windows版本)
REM
REM 用途: 启动Nexus服务器并运行压力测试
REM 版本: 1.0.0

setlocal enabledelayedexpansion

echo ========================================================================
echo Nexus Protocol 压力测试套件
echo ========================================================================
echo.

REM 检查Python环境
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [✓] Python版本: %PYTHON_VERSION%

REM 检查依赖
echo.
echo 检查依赖包...
python -c "import fastapi, uvicorn, socketio, pytest" >nul 2>&1
if errorlevel 1 (
    echo [警告] 缺少依赖包
    echo 正在安装依赖...
    pip install -r requirements.txt
) else (
    echo [✓] 所有依赖已安装
)

REM 检查服务器是否运行
echo.
echo 检查Nexus服务器状态...
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo [⚠] Nexus服务器未运行
    set SERVER_RUNNING=false
) else (
    echo [✓] Nexus服务器已运行
    set SERVER_RUNNING=true
)

REM 如果服务器未运行，询问是否启动
if "%SERVER_RUNNING%"=="false" (
    echo.
    set /p START_SERVER="是否启动Nexus服务器? (y/n): "
    if /i "!START_SERVER!"=="y" (
        echo 启动Nexus服务器...
        start /b python nexus_server.py > nexus_server.log 2>&1

        echo 等待服务器启动...
        timeout /t 5 /nobreak >nul

        curl -s http://localhost:8001/health >nul 2>&1
        if errorlevel 1 (
            echo [错误] 服务器启动失败
            exit /b 1
        ) else (
            echo [✓] 服务器启动成功
        )
    ) else (
        echo [错误] 需要运行Nexus服务器才能执行压力测试
        exit /b 1
    )
)

REM 选择测试级别
echo.
echo ========================================================================
echo 选择测试级别:
echo   1) quick    - 快速测试 (5-10分钟)
echo   2) standard - 标准测试 (20-30分钟)
echo   3) full     - 完整测试 (1-2小时)
echo ========================================================================
set /p LEVEL_CHOICE="请选择 [1-3] (默认: 1): "

if "%LEVEL_CHOICE%"=="2" (
    set TEST_LEVEL=standard
) else if "%LEVEL_CHOICE%"=="3" (
    set TEST_LEVEL=full
) else (
    set TEST_LEVEL=quick
)

echo [✓] 选择的测试级别: %TEST_LEVEL%

REM 选择测试类型
echo.
echo ========================================================================
echo 选择测试类型:
echo   1) all        - 所有测试
echo   2) concurrent - 并发连接测试
echo   3) throughput - 消息吞吐量测试
echo   4) longrun    - 长时间运行测试
echo   5) memory     - 内存泄漏检测
echo ========================================================================
set /p TEST_CHOICE="请选择 [1-5] (默认: 1): "

if "%TEST_CHOICE%"=="2" (
    set TEST_TYPE=concurrent
) else if "%TEST_CHOICE%"=="3" (
    set TEST_TYPE=throughput
) else if "%TEST_CHOICE%"=="4" (
    set TEST_TYPE=longrun
) else if "%TEST_CHOICE%"=="5" (
    set TEST_TYPE=memory
) else (
    set TEST_TYPE=all
)

echo [✓] 选择的测试类型: %TEST_TYPE%

REM 运行测试
echo.
echo ========================================================================
echo 开始压力测试
echo ========================================================================
echo 测试级别: %TEST_LEVEL%
echo 测试类型: %TEST_TYPE%
echo 开始时间: %date% %time%
echo ========================================================================
echo.

REM 执行测试
python tests\run_stress_tests.py --level %TEST_LEVEL% --test %TEST_TYPE% --verbose

set TEST_RESULT=%errorlevel%

REM 测试完成
echo.
echo ========================================================================
echo 测试完成
echo ========================================================================
echo 结束时间: %date% %time%

if %TEST_RESULT%==0 (
    echo [✅] 所有测试通过
) else (
    echo [❌] 部分测试失败 (退出码: %TEST_RESULT%^)
)

echo.
echo ========================================================================
echo 查看详细报告: PERFORMANCE_REPORT.md
echo ========================================================================

exit /b %TEST_RESULT%
