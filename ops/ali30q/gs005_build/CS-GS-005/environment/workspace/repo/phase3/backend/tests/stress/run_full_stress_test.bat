@echo off
REM 生产环境压力测试完整流程脚本 (Windows版本)
REM
REM 此脚本自动化执行完整的压力测试流程：
REM 1. 启动资源监控
REM 2. 执行压力测试
REM 3. 分析测试结果
REM 4. 生成综合报告
REM
REM 使用方式:
REM   run_full_stress_test.bat light
REM   run_full_stress_test.bat medium
REM   run_full_stress_test.bat heavy

setlocal enabledelayedexpansion

REM 配置
set SCRIPT_DIR=%~dp0
set RESULTS_DIR=%SCRIPT_DIR%results
set BACKEND_DIR=%SCRIPT_DIR%..\..
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM 默认参数
set TEST_LEVEL=%1
if "%TEST_LEVEL%"=="" set TEST_LEVEL=light

set API_HOST=%2
if "%API_HOST%"=="" set API_HOST=http://localhost:8000

echo ================================================================================
echo 生产环境压力测试完整流程
echo ================================================================================
echo 测试级别: %TEST_LEVEL%
echo 目标主机: %API_HOST%
echo 时间戳: %TIMESTAMP%
echo ================================================================================
echo.

REM 创建结果目录
if not exist "%RESULTS_DIR%" mkdir "%RESULTS_DIR%"

REM 检查Python
echo [INFO] 检查依赖...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python未安装
    exit /b 1
)

REM 检查Locust
python -c "import locust" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Locust未安装，请运行: pip install locust
    exit /b 1
)

REM 检查psutil
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo [WARN] psutil未安装，资源监控将被跳过
    set SKIP_MONITORING=true
)

echo [INFO] 依赖检查完成

REM 检查服务器状态
echo [INFO] 检查服务器状态: %API_HOST%
curl -s -f "%API_HOST%/health" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 无法连接到服务器: %API_HOST%
    echo [ERROR] 请确保服务器正在运行
    exit /b 1
)
echo [INFO] 服务器运行正常

REM 启动资源监控
if not "%SKIP_MONITORING%"=="true" (
    echo [INFO] 启动资源监控...

    REM 根据测试级别确定监控时长
    if "%TEST_LEVEL%"=="light" set MONITOR_DURATION=600
    if "%TEST_LEVEL%"=="medium" set MONITOR_DURATION=900
    if "%TEST_LEVEL%"=="heavy" set MONITOR_DURATION=1200
    if "%TEST_LEVEL%"=="peak" set MONITOR_DURATION=900
    if "%TEST_LEVEL%"=="endurance" set MONITOR_DURATION=3600

    start /B python "%SCRIPT_DIR%monitor_resources.py" --duration !MONITOR_DURATION! --interval 5 --api-url "%API_HOST%" > "%RESULTS_DIR%\monitor_%TEST_LEVEL%_%TIMESTAMP%.log" 2>&1

    echo [INFO] 资源监控已启动
    timeout /t 2 /nobreak >nul
)

REM 运行压力测试
echo [INFO] 运行压力测试: %TEST_LEVEL%
echo [INFO] 目标主机: %API_HOST%

cd /d "%BACKEND_DIR%"
python "%SCRIPT_DIR%run_production_tests.py" --level "%TEST_LEVEL%" --host "%API_HOST%"

if errorlevel 1 (
    echo [ERROR] 压力测试失败
    exit /b 1
)

echo [INFO] 压力测试完成

REM 等待监控完成
if not "%SKIP_MONITORING%"=="true" (
    echo [INFO] 等待资源监控完成...
    timeout /t 5 /nobreak >nul
    echo [INFO] 资源监控已完成
)

REM 分析测试结果
echo [INFO] 分析测试结果...

REM 查找最新的stats文件
for /f "delims=" %%i in ('dir /b /o-d "%RESULTS_DIR%\production_%TEST_LEVEL%_*_stats.csv" 2^>nul') do (
    set LATEST_STATS=%RESULTS_DIR%\%%i
    goto :found_stats
)
:found_stats

if not defined LATEST_STATS (
    echo [WARN] 未找到测试结果文件
    goto :skip_analysis
)

echo [INFO] 分析文件: %LATEST_STATS%
python "%SCRIPT_DIR%analyze_test_results.py" --csv "%LATEST_STATS%"
echo [INFO] 结果分析完成

:skip_analysis

REM 生成综合报告
echo [INFO] 生成测试摘要...

set SUMMARY_FILE=%RESULTS_DIR%\summary_%TEST_LEVEL%_%TIMESTAMP%.txt

echo ================================================================================ > "%SUMMARY_FILE%"
echo 生产环境压力测试摘要 >> "%SUMMARY_FILE%"
echo ================================================================================ >> "%SUMMARY_FILE%"
echo 测试时间: %date% %time% >> "%SUMMARY_FILE%"
echo 测试级别: %TEST_LEVEL% >> "%SUMMARY_FILE%"
echo 目标主机: %API_HOST% >> "%SUMMARY_FILE%"
echo ================================================================================ >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"
echo 测试文件: >> "%SUMMARY_FILE%"
dir "%RESULTS_DIR%\production_%TEST_LEVEL%_*%TIMESTAMP%*" 2>nul >> "%SUMMARY_FILE%"
dir "%RESULTS_DIR%\monitor_%TEST_LEVEL%_%TIMESTAMP%*" 2>nul >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"
echo ================================================================================ >> "%SUMMARY_FILE%"

echo [INFO] 摘要已保存到: %SUMMARY_FILE%
type "%SUMMARY_FILE%"

echo.
echo [INFO] 测试流程完成！
echo.

endlocal
