@echo off
rem Start school frontend dev server in a minimized, detached window
cd /d %~dp0
if not exist ..\logs mkdir ..\logs
start "gansu-school-dev" /min cmd /c "npm run dev > ..\logs\school-dev.out 2>&1"
echo [start_dev] school dev server starting... log: logs\school-dev.out
