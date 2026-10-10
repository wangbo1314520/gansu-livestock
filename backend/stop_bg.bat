@echo off
rem ============================================================
rem gansu-livestock backend stop script: kill PID listening on 5000
rem ============================================================
setlocal enabledelayedexpansion
set FOUND=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":5000 .*LISTENING"') do (
  taskkill /F /PID %%p >nul 2>&1
  echo [stop_bg] Killed PID %%p
  set FOUND=1
)
if "%FOUND%"=="0" echo [stop_bg] No process listening on port 5000
endlocal
