@echo off
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0stop-dev.ps1"
if errorlevel 1 pause
