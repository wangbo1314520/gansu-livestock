@echo off
rem ============================================================
rem gansu-livestock backend background start script
rem Password NOT stored here: inherited from env var DB_PASSWORD
rem Usage (CMD):
rem   set DB_PASSWORD=your_mysql_password
rem   E:\Program\gansu-livestock\backend\start_bg.bat
rem Log file: logs\backend.out
rem ============================================================
cd /d %~dp0
if not exist logs mkdir logs

if "%DB_PASSWORD%"=="" (
  echo [start_bg] Missing env var DB_PASSWORD. Run: set DB_PASSWORD=***
  exit /b 1
)

start "gansu-livestock-backend" /min cmd /c "venv\Scripts\python.exe app.py > logs\backend.out 2>&1"
echo [start_bg] Backend started in background. Log: logs\backend.out  Health: http://127.0.0.1:5000/api/health
