@echo off
rem compass daemon · 新版 daemon.py + 短路径 torch(C:/pylibs,治 WinError 206)
set PYTHONPATH=C:/pylibs
set PYTHONIOENCODING=utf-8
cd /d C:\Users\chunx\Projects\nautilus-compass
python daemon.py
