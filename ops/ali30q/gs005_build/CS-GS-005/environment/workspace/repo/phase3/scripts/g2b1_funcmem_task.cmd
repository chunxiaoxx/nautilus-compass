@echo off
cd /d C:\Users\chunx\Projects\nautilus-core\phase3\backend
if not exist docs\evidence\g2b1_funcmem_20260908 mkdir docs\evidence\g2b1_funcmem_20260908
for /f "tokens=1,* delims==" %%a in ('findstr /b "CHUNXIAO_API_KEY=" ".env"') do set "%%a=%%b"
python -u tools\g2_b1_func_mem_experiment.py > docs\evidence\g2b1_funcmem_20260908\run1.log 2>&1
