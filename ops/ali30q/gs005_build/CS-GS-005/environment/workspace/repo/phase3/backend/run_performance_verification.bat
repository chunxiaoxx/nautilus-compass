@echo off
REM Application Performance Verification Script for Windows
REM 应用性能验证脚本 (Windows)

echo ================================================================================
echo NAUTILUS PHASE 3 - 应用性能验证
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/7] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: Python未安装或未添加到PATH
    pause
    exit /b 1
)

echo.
echo [2/7] 检查依赖...
python -c "import fastapi, sqlalchemy, uvicorn" 2>nul
if errorlevel 1 (
    echo 警告: 部分依赖未安装，正在安装...
    pip install -r requirements.txt
)

echo.
echo [3/7] 运行性能验证脚本...
echo.
python verify_application_performance.py

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo 验证失败! 请检查错误信息
    echo ================================================================================
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo 验证完成!
echo ================================================================================
echo.
echo 查看详细报告: APPLICATION_PERFORMANCE_REPORT.md
echo.

pause
