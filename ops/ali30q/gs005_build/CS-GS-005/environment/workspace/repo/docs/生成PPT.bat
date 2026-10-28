@echo off
echo =================
echo Nautilus PPT 一键生成脚本
echo ==============================
echo.

cd /d C:\Users\chunx\Projects\nautilus-core\docs

echo 正在检查依赖...
pip show python-pptx >nul 2>&1
if errorlevel 1 (
    echo 安装依赖包...
    pip install python-pptx pillow google-generativeai
) else (
    echo 依赖包已安装
)

echo.
echo 请选择生成方案:
echo 1. 基础版 (5分钟, 无图片)
echo 2. Gemini增强版 (30分钟, 含AI图片)
echo.
set /p choice=请输入选择 (1 或 2):

if "%choice%"=="1" (
    echo.
    echo 正在生成基础版PPT...
  python generate_pitch_deck.py
    if errorlevel 0 (
        echo.
        echo ✅ 生成成功！
        echo 正在打开PPT...
        start Nautilus_Pitch_Deck_CN.pptx
    )
) else if "%choice%"=="2" (
    echo.
    echo 正在生成Gemini增强版PPT...
    python generate_pitch_deck_gemini.py
    if errorlevel 0 (
    echo.
        echo ✅ 生成成功！
        echo 正在打开PPT...
        start Nautilus_Pitch_Deck_with_Images.pptx
    )
) else (
    echo 无效选择
)

echo.
pause
