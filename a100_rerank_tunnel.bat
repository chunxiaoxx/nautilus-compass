@echo off
rem A100 rerank 隧道保活(R497 拍板即时部署 · 用户令"现在就开")
rem 本机 127.0.0.1:19879 -> A100 127.0.0.1:9879 (GPU bge-reranker-v2-m3)
:loop
python "%~dp0a100_rerank_tunnel.py"
timeout /t 10 /nobreak >nul
goto loop
