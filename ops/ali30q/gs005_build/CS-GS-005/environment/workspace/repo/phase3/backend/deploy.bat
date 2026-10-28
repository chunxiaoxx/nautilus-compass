@echo off
REM Nexus Server Docker 部署脚本 (Windows)

setlocal enabledelayedexpansion

REM 检查Docker是否安装
echo [INFO] 检查Docker安装...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未安装，请先安装Docker Desktop
    exit /b 1
)
echo [INFO] Docker已安装

REM 检查Docker Compose是否安装
echo [INFO] 检查Docker Compose安装...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose未安装
    exit /b 1
)
echo [INFO] Docker Compose已安装

:menu
echo.
echo ================================
echo   Nexus Server Docker 部署工具
echo ================================
echo 1. 构建镜像
echo 2. 启动服务
echo 3. 停止服务
echo 4. 重启服务
echo 5. 查看日志
echo 6. 查看状态
echo 7. 健康检查
echo 8. 完整部署（构建+启动+检查）
echo 9. 清理资源
echo 0. 退出
echo ================================
echo.

set /p choice="请选择操作 [0-9]: "

if "%choice%"=="1" goto build
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto restart
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto status
if "%choice%"=="7" goto health
if "%choice%"=="8" goto deploy
if "%choice%"=="9" goto cleanup
if "%choice%"=="0" goto exit
goto menu

:build
echo [INFO] 构建Docker镜像...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] 镜像构建失败
    pause
    goto menu
)
echo [INFO] 镜像构建完成
pause
goto menu

:start
echo [INFO] 启动Nexus服务...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] 服务启动失败
    pause
    goto menu
)
echo [INFO] 服务启动完成
pause
goto menu

:stop
echo [INFO] 停止服务...
docker-compose down
echo [INFO] 服务已停止
pause
goto menu

:restart
echo [INFO] 重启服务...
docker-compose down
docker-compose up -d
echo [INFO] 服务重启完成
pause
goto menu

:logs
echo [INFO] 显示服务日志...
docker-compose logs --tail=50
pause
goto menu

:status
echo [INFO] 查看服务状态...
docker-compose ps
pause
goto menu

:health
echo [INFO] 检查服务健康状态...
timeout /t 5 /nobreak >nul
curl -f http://localhost:8001/health
if errorlevel 1 (
    echo [ERROR] 健康检查失败
) else (
    echo [INFO] 健康检查通过
)
pause
goto menu

:deploy
echo [INFO] 开始完整部署...
call :build
call :start
echo [INFO] 等待服务启动...
timeout /t 10 /nobreak >nul
call :health
echo [INFO] 部署完成
pause
goto menu

:cleanup
echo [INFO] 清理Docker资源...
docker-compose down -v
docker system prune -f
echo [INFO] 清理完成
pause
goto menu

:exit
echo [INFO] 退出部署工具
exit /b 0
