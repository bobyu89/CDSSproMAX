@echo off
REM Double-click launcher for TICDSS dev environment.
REM Bypasses execution policy so the .ps1 always runs.
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0start-dev.ps1"
if errorlevel 1 pause
