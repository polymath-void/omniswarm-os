<#
.SYNOPSIS
    OmniSwarm PC Hub 24/7 Background Daemonizer (Windows PowerShell)
.DESCRIPTION
    Manages the OmniOS Root Kernel daemon (port 5565), persistent Bore tunnel
    (bore.pub:33458), and the PCAgent autonomous loop as background services with
    PID tracking, auto-restart, logging, and Windows Startup auto-boot capability.
.EXAMPLE
    .\daemonize_hub.ps1 start
    .\daemonize_hub.ps1 status
    .\daemonize_hub.ps1 stop
    .\daemonize_hub.ps1 restart
    .\daemonize_hub.ps1 enable-autoboot
    .\daemonize_hub.ps1 disable-autoboot
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status", "restart", "enable-autoboot", "disable-autoboot")]
    [string]$Action = "status"
)

$WORKSPACE = $PSScriptRoot
if (-not $WORKSPACE) { $WORKSPACE = Get-Location }
Set-Location $WORKSPACE

# Paths
$VENV_PYTHON = Join-Path $WORKSPACE ".omnios_venv\Scripts\python.exe"
if (-not (Test-Path $VENV_PYTHON)) {
    $VENV_PYTHON = "python.exe"
}
$DAEMON_SCRIPT = Join-Path $WORKSPACE "omniswarm_py\omniswarm_daemon.py"
$AGENT_SCRIPT  = Join-Path $WORKSPACE "pc_agent.py"
$BORE_EXE      = Join-Path $WORKSPACE "bore.exe"

$HUB_PID_FILE   = Join-Path $WORKSPACE ".hub_daemon.pid"
$BORE_PID_FILE  = Join-Path $WORKSPACE ".bore_tunnel.pid"
$AGENT_PID_FILE = Join-Path $WORKSPACE ".pc_agent.pid"

$HUB_LOG        = Join-Path $WORKSPACE "hub_daemon.log"
$HUB_ERR_LOG    = Join-Path $WORKSPACE "hub_daemon_err.log"
$BORE_LOG       = Join-Path $WORKSPACE "bore_tunnel.log"
$AGENT_LOG      = Join-Path $WORKSPACE "pc_agent.log"

$STARTUP_LNK = Join-Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup" "OmniSwarm_Hub.lnk"
$SILENT_VBS  = Join-Path $WORKSPACE "start_hub_silent.vbs"

function Is-ProcessRunning([int]$pidToCheck) {
    if ($pidToCheck -le 0) { return $false }
    $p = Get-Process -Id $pidToCheck -ErrorAction SilentlyContinue
    return ($null -ne $p)
}

function Get-StoredPid([string]$pidFilePath) {
    if (Test-Path $pidFilePath) {
        $content = (Get-Content $pidFilePath -ErrorAction SilentlyContinue | Out-String).Trim()
        if ($content -match '^\d+$') {
            return [int]$content
        }
    }
    return 0
}

function Start-Hub {
    Write-Host "`n>>> [OmniSwarm PC Hub] Starting 24/7 Background Services..." -ForegroundColor Cyan

    # 1. Start OmniOS Root Kernel
    $hubPid = Get-StoredPid $HUB_PID_FILE
    if ($hubPid -gt 0 -and (Is-ProcessRunning $hubPid)) {
        Write-Host "    [OK] OmniOS Root Kernel is already running (PID: $hubPid)" -ForegroundColor Green
    } else {
        Write-Host "    Launching OmniOS Root Kernel on port 5565..." -ForegroundColor Yellow
        $hubProc = Start-Process -FilePath $VENV_PYTHON `
            -ArgumentList "-u `"$DAEMON_SCRIPT`"" `
            -WorkingDirectory $WORKSPACE `
            -WindowStyle Hidden `
            -PassThru `
            -RedirectStandardOutput $HUB_LOG `
            -RedirectStandardError $HUB_ERR_LOG

        if ($hubProc) {
            Set-Content -Path $HUB_PID_FILE -Value $hubProc.Id -Force
            Write-Host "    [OK] OmniOS Root Kernel started (PID: $($hubProc.Id))" -ForegroundColor Green
        } else {
            Write-Host "    [ERROR] Failed to start OmniOS Root Kernel" -ForegroundColor Red
        }
    }

    # 2. Start Persistent Bore Tunnel
    $borePid = Get-StoredPid $BORE_PID_FILE
    $boreRunning = $borePid -gt 0 -and (Is-ProcessRunning $borePid)
    $boreExeRunning = (Get-Process -Name "bore" -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0

    if ($boreRunning -and $boreExeRunning) {
        Write-Host "    [OK] Bore Tunnel Watchdog is already running (PID: $borePid)" -ForegroundColor Green
    } else {
        Write-Host "    Launching Bore Tunnel Watchdog (bore.pub:33458 -> localhost:5565)..." -ForegroundColor Yellow
        $watchdogScript = "while (`$true) { Write-Output `"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Starting bore tunnel on 33458...`"; & `'$BORE_EXE`' local 5565 --to bore.pub --port 33458 *>> `'$BORE_LOG`'; Start-Sleep -Seconds 2 }"
        
        $boreProc = Start-Process -FilePath "powershell.exe" `
            -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"$watchdogScript`"" `
            -WorkingDirectory $WORKSPACE `
            -WindowStyle Hidden `
            -PassThru

        if ($boreProc) {
            Set-Content -Path $BORE_PID_FILE -Value $boreProc.Id -Force
            Write-Host "    [OK] Bore Tunnel Watchdog started (PID: $($boreProc.Id))" -ForegroundColor Green
        } else {
            Write-Host "    [ERROR] Failed to start Bore Tunnel Watchdog" -ForegroundColor Red
        }
    }

    # 3. Start PCAgent Autonomous Loop (if --loop-only supported)
    $agentPid = Get-StoredPid $AGENT_PID_FILE
    if ($agentPid -gt 0 -and (Is-ProcessRunning $agentPid)) {
        Write-Host "    [OK] PCAgent Autonomous Loop is already running (PID: $agentPid)" -ForegroundColor Green
    } else {
        Write-Host "    Launching PCAgent Autonomous Loop..." -ForegroundColor Yellow
        $agentProc = Start-Process -FilePath $VENV_PYTHON `
            -ArgumentList "-u `"$AGENT_SCRIPT`" --loop-only" `
            -WorkingDirectory $WORKSPACE `
            -WindowStyle Hidden `
            -PassThru `
            -RedirectStandardOutput $AGENT_LOG `
            -RedirectStandardError (Join-Path $WORKSPACE "pc_agent_err.log")

        if ($agentProc) {
            Set-Content -Path $AGENT_PID_FILE -Value $agentProc.Id -Force
            Write-Host "    [OK] PCAgent Autonomous Loop started (PID: $($agentProc.Id))" -ForegroundColor Green
        }
    }

    # Verify Port 5565
    Start-Sleep -Seconds 2
    $conn = Get-NetTCPConnection -LocalPort 5565 -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "`n    [OK] OmniOS Kernel listening on port 5565 (Virtual Hub: bore.pub:33458)" -ForegroundColor Green
    } else {
        Write-Host "`n    [WARN] Port 5565 not listening yet. Check $HUB_LOG for details." -ForegroundColor Yellow
    }
}

function Stop-Hub {
    Write-Host "`n>>> [OmniSwarm PC Hub] Stopping Background Services..." -ForegroundColor Cyan

    # 1. Stop PCAgent Loop
    $agentPid = Get-StoredPid $AGENT_PID_FILE
    if ($agentPid -gt 0) {
        Stop-Process -Id $agentPid -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $AGENT_PID_FILE) { Remove-Item $AGENT_PID_FILE -Force -ErrorAction SilentlyContinue }
    Write-Host "    [OK] PCAgent Loop stopped." -ForegroundColor Green

    # 2. Stop Bore Watchdog and bore.exe processes
    $borePid = Get-StoredPid $BORE_PID_FILE
    if ($borePid -gt 0) {
        Stop-Process -Id $borePid -Force -ErrorAction SilentlyContinue
    }
    Get-Process -Name "bore" -ErrorAction SilentlyContinue | Stop-Process -Force
    if (Test-Path $BORE_PID_FILE) { Remove-Item $BORE_PID_FILE -Force -ErrorAction SilentlyContinue }
    Write-Host "    [OK] Bore Tunnel stopped." -ForegroundColor Green

    # 3. Stop OmniOS Root Kernel
    $hubPid = Get-StoredPid $HUB_PID_FILE
    if ($hubPid -gt 0) {
        Stop-Process -Id $hubPid -Force -ErrorAction SilentlyContinue
    }
    Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%omniswarm_daemon.py%'" -ErrorAction SilentlyContinue | 
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if (Test-Path $HUB_PID_FILE) { Remove-Item $HUB_PID_FILE -Force -ErrorAction SilentlyContinue }
    Write-Host "    [OK] OmniOS Root Kernel stopped." -ForegroundColor Green
}

function Get-HubStatus {
    Write-Host "`n=======================================================" -ForegroundColor Magenta
    Write-Host "     [OMNISWARM PC HUB 24/7 BACKGROUND STATUS]        " -ForegroundColor Magenta
    Write-Host "=======================================================" -ForegroundColor Magenta

    # Check Kernel
    $hubPid = Get-StoredPid $HUB_PID_FILE
    $hubRunning = $hubPid -gt 0 -and (Is-ProcessRunning $hubPid)
    $port5565 = Get-NetTCPConnection -LocalPort 5565 -State Listen -ErrorAction SilentlyContinue

    if ($hubRunning -or $port5565) {
        Write-Host "`n[OmniOS Kernel]     : [ONLINE]" -ForegroundColor Green
        Write-Host "  PID               : $(if ($hubRunning) { $hubPid } else { 'External' })"
        Write-Host "  Port 5565 (RPC)   : $(if ($port5565) { 'LISTENING' } else { 'WAITING' })"
    } else {
        Write-Host "`n[OmniOS Kernel]     : [STOPPED]" -ForegroundColor Red
    }

    # Check Bore Tunnel
    $borePid = Get-StoredPid $BORE_PID_FILE
    $boreRunning = (Get-Process -Name "bore" -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0
    if ($boreRunning) {
        Write-Host "`n[Bore Tunnel]       : [ONLINE]" -ForegroundColor Green
        Write-Host "  Endpoint          : bore.pub:33458 -> localhost:5565"
        Write-Host "  Watchdog PID      : $(if ($borePid -gt 0) { $borePid } else { 'External' })"
    } else {
        Write-Host "`n[Bore Tunnel]       : [STOPPED]" -ForegroundColor Red
    }

    # Check PCAgent Loop
    $agentPid = Get-StoredPid $AGENT_PID_FILE
    $agentRunning = $agentPid -gt 0 -and (Is-ProcessRunning $agentPid)
    if ($agentRunning) {
        Write-Host "`n[PCAgent Loop]      : [ONLINE]" -ForegroundColor Green
        Write-Host "  PID               : $agentPid"
    } else {
        Write-Host "`n[PCAgent Loop]      : [STOPPED]" -ForegroundColor Red
    }

    # Check Windows Startup
    $autoboot = Test-Path $STARTUP_LNK
    Write-Host "`n[Windows Auto-Boot] : $(if ($autoboot) { '[ENABLED]' } else { '[DISABLED]' })"

    # Show Tail Logs
    if (Test-Path $HUB_LOG) {
        Write-Host "`n--- Recent Kernel Log ($HUB_LOG) ---" -ForegroundColor Cyan
        Get-Content $HUB_LOG -Tail 5 -ErrorAction SilentlyContinue
    }
    if (Test-Path $BORE_LOG) {
        Write-Host "`n--- Recent Bore Log ($BORE_LOG) ---" -ForegroundColor Cyan
        Get-Content $BORE_LOG -Tail 5 -ErrorAction SilentlyContinue
    }
    Write-Host "=======================================================`n" -ForegroundColor Magenta
}

function Enable-AutoBoot {
    Write-Host "`n>>> [OmniSwarm PC Hub] Configuring Windows Startup Auto-Boot..." -ForegroundColor Cyan
    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($STARTUP_LNK)
    $shortcut.TargetPath = "wscript.exe"
    $shortcut.Arguments = "`"$SILENT_VBS`""
    $shortcut.WorkingDirectory = $WORKSPACE
    $shortcut.Description = "OmniSwarm PC Hub Silent Background Daemon"
    $shortcut.Save()
    Write-Host "    [OK] Auto-Boot shortcut installed to: $STARTUP_LNK" -ForegroundColor Green
    Write-Host "    OmniSwarm PC Hub will now launch automatically on Windows login!" -ForegroundColor Green
}

function Disable-AutoBoot {
    Write-Host "`n>>> [OmniSwarm PC Hub] Disabling Windows Startup Auto-Boot..." -ForegroundColor Cyan
    if (Test-Path $STARTUP_LNK) {
        Remove-Item $STARTUP_LNK -Force
        Write-Host "    [OK] Auto-Boot shortcut removed." -ForegroundColor Green
    } else {
        Write-Host "    Auto-Boot was not enabled." -ForegroundColor Yellow
    }
}

switch ($Action) {
    "start"            { Start-Hub }
    "stop"             { Stop-Hub }
    "status"           { Get-HubStatus }
    "restart"          { Stop-Hub; Start-Sleep -Seconds 2; Start-Hub }
    "enable-autoboot"  { Enable-AutoBoot }
    "disable-autoboot" { Disable-AutoBoot }
}
