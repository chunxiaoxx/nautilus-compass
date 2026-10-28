@echo off
REM Nautilus Phase 3 Backend - 安全修复快速部署脚本 (Windows)
REM 版本: 1.0
REM 日期: 2026-02-26

setlocal enabledelayedexpansion

echo ========================================
echo Nautilus Phase 3 Backend - 安全修复部署
echo ========================================
echo.

REM 检查Python
echo [1/7] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到PATH
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [成功] Python版本: %PYTHON_VERSION%
echo.

REM 检查虚拟环境
echo [2/7] 检查虚拟环境...
if exist "venv\" (
    echo [成功] 虚拟环境已存在
) else (
    echo [警告] 虚拟环境不存在，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建成功
)
echo.

REM 激活虚拟环境
echo [3/7] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)
echo [成功] 虚拟环境已激活
echo.

REM 升级pip
echo [4/7] 升级pip...
python -m pip install --upgrade pip --quiet
echo [成功] pip已升级
echo.

REM 安装依赖
echo [5/7] 安装依赖包...
echo 这可能需要几分钟时间...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [成功] 依赖安装完成
echo.

REM 验证安全依赖
echo 验证安全依赖...
pip list | findstr /C:"slowapi" >nul
if errorlevel 1 (
    echo [错误] slowapi未安装
    pause
    exit /b 1
)
pip list | findstr /C:"fastapi-csrf-protect" >nul
if errorlevel 1 (
    echo [错误] fastapi-csrf-protect未安装
    pause
    exit /b 1
)
echo [成功] 安全依赖验证通过
echo.

REM 生成密钥
echo [6/7] 生成安全密钥...
for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set CSRF_KEY=%%i
for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set JWT_KEY=%%i
echo [成功] 密钥已生成
echo.

REM 配置环境变量
echo [7/7] 配置环境变量...
if not exist ".env" (
    echo [警告] .env文件不存在，从.env.example复制...
    copy .env.example .env >nul
    echo [成功] .env文件已创建
) else (
    echo [信息] .env文件已存在
)

REM 检查并添加必需的环境变量
findstr /C:"ALLOWED_ORIGINS" .env >nul
if errorlevel 1 (
    echo ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001 >> .env
    echo [成功] 已添加 ALLOWED_ORIGINS
)

findstr /C:"CSRF_SECRET_KEY" .env >nul
if errorlevel 1 (
    echo CSRF_SECRET_KEY=%CSRF_KEY% >> .env
    echo [成功] 已添加 CSRF_SECRET_KEY
)

findstr /C:"RATE_LIMIT_ENABLED" .env >nul
if errorlevel 1 (
    echo RATE_LIMIT_ENABLED=true >> .env
    echo [成功] 已添加 RATE_LIMIT_ENABLED
)

echo [成功] 环境变量配置完成
echo.

REM 验证代码
echo 验证代码...
python -c "from main import app; print('导入成功')" >nul 2>&1
if errorlevel 1 (
    echo [错误] main.py导入失败
    pause
    exit /b 1
)
echo [成功] 代码验证通过
echo.

REM 打印摘要
echo ========================================
echo 部署摘要
echo ========================================
echo.
echo [成功] 安全修复部署完成!
echo.
echo 已实施的安全措施:
echo   1. [√] API速率限制
echo   2. [√] CORS源限制
echo   3. [√] CSRF防护
echo   4. [√] 安全HTTP头部
echo.
echo 生成的密钥 (请保存到安全位置):
echo   CSRF_SECRET_KEY=%CSRF_KEY%
echo   JWT_SECRET_KEY=%JWT_KEY%
echo.
echo 下一步:
echo   1. 检查 .env 文件配置
echo   2. 启动服务: python main.py
echo   3. 运行安全测试: python test_security_fixes.py
echo   4. 查看报告: SECURITY_FIXES_REPORT.md
echo   5. 查看检查清单: DEPLOYMENT_CHECKLIST.md
echo.
echo 有用的命令:
echo   - 启动服务: python main.py
echo   - 运行测试: pytest tests/
echo   - 安全测试: python test_security_fixes.py
echo.

REM 询问是否启动服务
set /p START_SERVER="是否启动开发服务器? (y/n): "
if /i "%START_SERVER%"=="y" (
    echo.
    echo 启动服务器...
    echo 访问: http://localhost:8000
    echo API文档: http://localhost:8000/docs
    echo 按 Ctrl+C 停止服务器
    echo.
    python main.py
) else (
    echo.
    echo 跳过启动服务器
    echo 手动启动命令: python main.py
    echo.
)

pause
