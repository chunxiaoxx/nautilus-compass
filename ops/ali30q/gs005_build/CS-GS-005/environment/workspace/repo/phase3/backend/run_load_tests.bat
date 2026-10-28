@echo off
REM Locust压力测试快速启动脚本 (Windows版本)
REM 用于快速运行不同的负载测试场景

setlocal enabledelayedexpansion

REM 检查Locust是否安装
where locust >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Locust未安装
    echo [INFO] 请运行: pip install locust
    exit /b 1
)

REM 默认参数
set SCENARIO=%1
set HOST=http://localhost:8000
set WEB_MODE=false
set GENERATE_REPORT=true

REM 检查场景参数
if "%SCENARIO%"=="" (
    echo [ERROR] 请指定测试场景
    call :show_usage
    exit /b 1
)

if "%SCENARIO%"=="--help" (
    call :show_usage
    exit /b 0
)

REM 解析其他参数
:parse_args
shift
if "%1"=="" goto :end_parse
if "%1"=="--host" (
    set HOST=%2
    shift
    goto :parse_args
)
if "%1"=="--web" (
    set WEB_MODE=true
    goto :parse_args
)
if "%1"=="--no-report" (
    set GENERATE_REPORT=false
    goto :parse_args
)
shift
goto :parse_args
:end_parse

REM 检查后端服务
echo [INFO] 检查后端服务: %HOST%
curl -s -f "%HOST%/health" >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] 无法连接到后端服务: %HOST%
    echo [INFO] 请确保后端服务正在运行
    set /p CONTINUE="是否继续? (y/n): "
    if /i not "!CONTINUE!"=="y" exit /b 1
)

REM 根据场景设置参数
if "%SCENARIO%"=="light" (
    set USERS=10
    set SPAWN_RATE=2
    set RUN_TIME=5m
) else if "%SCENARIO%"=="medium" (
    set USERS=50
    set SPAWN_RATE=5
    set RUN_TIME=10m
) else if "%SCENARIO%"=="heavy" (
    set USERS=100
    set SPAWN_RATE=10
    set RUN_TIME=15m
) else if "%SCENARIO%"=="peak" (
    set USERS=200
    set SPAWN_RATE=20
    set RUN_TIME=10m
) else if "%SCENARIO%"=="stress" (
    set USERS=500
    set SPAWN_RATE=50
    set RUN_TIME=20m
) else if "%SCENARIO%"=="spike" (
    set USERS=300
    set SPAWN_RATE=100
    set RUN_TIME=5m
) else if "%SCENARIO%"=="endurance" (
    set USERS=30
    set SPAWN_RATE=3
    set RUN_TIME=60m
) else if "%SCENARIO%"=="custom" (
    set /p USERS="并发用户数: "
    set /p SPAWN_RATE="启动速率 (用户/秒): "
    set /p RUN_TIME="运行时间 (如: 10m, 1h): "
) else (
    echo [ERROR] 未知场景: %SCENARIO%
    call :show_usage
    exit /b 1
)

REM 显示测试信息
echo.
echo ==========================================
echo 场景: %SCENARIO%
echo 目标主机: %HOST%
echo 并发用户数: %USERS%
echo 启动速率: %SPAWN_RATE% 用户/秒
echo 运行时间: %RUN_TIME%
echo ==========================================
echo.

REM 构建命令
set CMD=locust -f locustfile.py --host=%HOST%

if "%WEB_MODE%"=="true" (
    REM Web界面模式
    echo [INFO] 启动Web界面模式...
    echo [INFO] 请访问: http://localhost:8089
    %CMD%
) else (
    REM 无头模式
    set CMD=%CMD% --users %USERS% --spawn-rate %SPAWN_RATE% --run-time %RUN_TIME% --headless

    REM 生成报告
    if "%GENERATE_REPORT%"=="true" (
        for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set DATE=%%c%%a%%b)
        for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set TIME=%%a%%b)
        set TIMESTAMP=!DATE!_!TIME!
        set REPORT_NAME=load_test_%SCENARIO%_!TIMESTAMP!

        REM 创建results目录
        if not exist results mkdir results

        set CMD=!CMD! --csv results/!REPORT_NAME! --html results/!REPORT_NAME!.html
        echo [INFO] 报告将保存到: results/!REPORT_NAME!.html
    )

    echo [INFO] 运行命令: !CMD!
    echo.

    REM 运行测试
    !CMD!
    if %errorlevel% equ 0 (
        echo [SUCCESS] 测试完成！
        if "%GENERATE_REPORT%"=="true" (
            echo [SUCCESS] 报告已保存: results/!REPORT_NAME!.html
        )
    ) else (
        echo [ERROR] 测试失败
        exit /b 1
    )
)

goto :eof

:show_usage
echo 用法: %~nx0 [scenario] [options]
echo.
echo 场景:
echo   light      - 轻负载测试 (10用户, 5分钟)
echo   medium     - 中负载测试 (50用户, 10分钟)
echo   heavy      - 重负载测试 (100用户, 15分钟)
echo   peak       - 峰值负载测试 (200用户, 10分钟)
echo   stress     - 压力测试 (500用户, 20分钟)
echo   spike      - 尖峰测试 (300用户, 5分钟)
echo   endurance  - 耐久测试 (30用户, 60分钟)
echo   custom     - 自定义测试
echo.
echo 选项:
echo   --host URL        - 目标主机 (默认: http://localhost:8000)
echo   --web             - 使用Web界面模式
echo   --no-report       - 不生成HTML报告
echo   --help            - 显示此帮助信息
echo.
echo 示例:
echo   %~nx0 light
echo   %~nx0 medium --host http://staging.example.com
echo   %~nx0 heavy --web
goto :eof
