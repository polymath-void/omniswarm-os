@echo off
REM ==============================================================================
REM OmniSwarm PC Hub 24/7 Background Manager (CMD Wrapper)
REM Usage: daemonize_hub.bat [start|stop|status|restart|enable-autoboot|disable-autoboot]
REM ==============================================================================
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0daemonize_hub.ps1" %*
endlocal
