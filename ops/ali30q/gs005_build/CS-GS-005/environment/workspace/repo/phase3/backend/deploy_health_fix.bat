@echo off
REM 数据库健康检查修复 - Windows 部署脚本
setlocal enabledelayedexpansion

set SERVER=ubuntu@115.159.62.192
set REMOTE_PATH=/home/ubuntu/nautilus-mvp/phase3/backend
set LOCAL_FILE=monitoring_config.py

echo ==========================================
echo Nautilus 数据库健康检查修复部署
echo ==========================================
echo.

REM 步骤 1: 备份远程文件
echo 📦 步骤 1/4: 备份远程文件...
ssh %SERVER% "cd %REMOTE_PATH% && cp monitoring_config.py monitoring_config.py.backup"
if errorlevel 1 (
    echo ❌ 备份失败
    exit /b 1
)
echo ✅ 备份完成
echo.

REM 步骤 2: 上传修复文件
echo 📤 步骤 2/4: 上传修复文件...
scp "%LOCAL_FILE%" "%SERVER%:%REMOTE_PATH%/"
if errorlevel 1 (
    echo ❌ 上传失败
    exit /b 1
)
echo ✅ 上传完成
echo.

REM 步骤 3: 重启服务
echo 🔄 步骤 3/4: 重启后端服务...
ssh %SERVER% "cd %REMOTE_PATH% && sudo systemctl restart nautilus-backend"
if errorlevel 1 (
    echo ❌ 重启失败
    exit /b 1
)
echo ⏳ 等待服务启动 (10秒)...
timeout /t 10 /nobreak >nul
echo ✅ 服务重启完成
echo.

REM 步骤 4: 验证修复
echo 🔍 步骤 4/4: 验证健康检查...
curl -s http://115.159.62.192:8000/health
echo.
echo.

echo ==========================================
echo 请检查上面的输出，确认:
echo 1. status = "healthy"
echo 2. database.connected = true
echo 3. database.status = "healthy"
echo ==========================================
echo.
echo 如需回滚，执行:
echo ssh %SERVER% "cd %REMOTE_PATH% && cp monitoring_config.py.backup monitoring_config.py && sudo systemctl restart nautilus-backend"
echo.

pause
