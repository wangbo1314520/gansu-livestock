@echo off
rem Start home frontend dev server (port 5174) in a minimized, detached window
cd /d %~dp0
if not exist ..\logs mkdir ..\logs
start "gansu-home-dev" /min cmd /c "npm run dev -- --port 5174 --strictPort > ..\logs\home-dev.out 2>&1"
echo [start_dev] home dev server starting on 5174... log: logs\home-dev.out
