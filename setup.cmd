@echo off
REM Double-click installer for TICDSS first-time setup.
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\setup.ps1"
pause
