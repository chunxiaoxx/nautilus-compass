@echo off
rem G2-B1 resident repair-executor daemon launcher
rem Started by Task Scheduler (nautilus-g2b1-daemon) at logon, or manually.
rem Policy: 2 tasks / 30 min per round, 500k tokens/day fail-closed cap.
cd /d C:\Users\chunx\Projects\nautilus-core\phase3\backend
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b "ARK_API_KEY=" "C:\Users\chunx\.claude\.cache\.fde_api_secrets.env"`) do set %%A=%%B
set "NAUTILUS_BACKEND_BASE=https://www.nautilus.social"
set "PYTHONIOENCODING=utf-8"
python tools\g2_b1_executor_agent.py --queue docs\evidence\g2b1_queue_rotated.jsonl --evidence-dir docs\evidence --provider ark_glm --limit 2 --daily-token-cap 500000 --loop-minutes 30 >> docs\evidence\.g2b1_daemon.log 2>&1
