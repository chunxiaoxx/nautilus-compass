@echo off
rem A100 rerank 隧道保活(R452 · compass_tunnel.bat 同款模式)
rem 本机 127.0.0.1:19879 -> A100 127.0.0.1:9879 (GPU bge-reranker-v2-m3)
rem daemon 接法: COMPASS_RERANK_REMOTE=127.0.0.1:19879
:loop
python "%~dp0a100_rerank_tunnel.py"
timeout /t 10 /nobreak >nul
goto loop
