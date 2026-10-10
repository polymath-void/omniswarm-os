@echo off
setlocal
cd /d "%~dp0"
echo Launching OmniSwarm-OS Windows Turnkey Installer...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
endlocal
