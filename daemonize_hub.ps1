# ==============================================================================
# OmniSwarm Hub 24/7 Background Daemonizer (Windows PowerShell)
# Manages OmniOS Root Kernel daemon, persistent Bore tunnel, and PCAgent loop.
# ==============================================================================
param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status", "restart")]
    [string]$Action = "status"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$HubPidFile = Join-Path $ScriptDir ".hub_daemon.pid"
$BorePidFile = Join-Path $ScriptDir ".bore_tunnel.pid"
$AgentPidFile = Join-Path $ScriptDir ".pc_agent.pid"

$HubLogFile = Join-Path $ScriptDir "hub_daemon.log"
$BoreLogFile = Join-Path $ScriptDir "bore_tunnel.log"
$AgentLogFile = Join-Path $ScriptDir "pc_agent.log"

# Locate Python environment (.omnios_venv preferred)
$PythonExe = Join-Path $ScriptDir ".omnios_venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

# Locate Bore binary
$BoreExe = Join-Path $ScriptDir "bore.exe"
if (-not (Test-Path $BoreExe)) {
    $BoreExe = "bore.exe"
}

function Test-ProcessAlive($pidFile) {
    if (Test-Path $pidFile) {
        $rawPid = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($rawPid) {
            $pId = [int]$rawPid
            $proc = Get-Process -Id $pId -ErrorAction SilentlyContinue
            if ($proc) { return $proc }
        }
    }
    return $null
}

function Start-Hub {
    Write-Host ">>> Starting OmniSwarm Hub 24/7 Services..." -ForegroundColor Cyan

    # 1. OmniOS Root Kernel Daemon (Port 5565)
    $hubProc = Test-ProcessAlive $HubPidFile
    if ($hubProc) {
        Write-Host "    • OmniOS Kernel already running (PID: $($hubProc.Id))" -ForegroundColor Yellow
    } else {
        $daemonScript = Join-Path $ScriptDir "omniswarm_py\omniswarm_daemon.py"
        $proc = Start-Process -FilePath $PythonExe -ArgumentList "-u", "`"$daemonScript`"" -RedirectStandardOutput $HubLogFile -RedirectStandardError $HubLogFile -WindowStyle Hidden -PassThru
        $proc.Id | Out-File -FilePath $HubPidFile -Encoding ascii
        Write-Host "    • OmniOS Kernel daemon started (PID: $($proc.Id))" -ForegroundColor Green
    }

    Start-Sleep -Seconds 1

    # 2. Persistent Bore TCP Tunnel (Port 5565 -> bore.pub:33458)
    $boreProc = Test-ProcessAlive $BorePidFile
    if ($boreProc) {
        Write-Host "    • Bore tunnel already running (PID: $($boreProc.Id))" -ForegroundColor Yellow
    } else {
        $proc = Start-Process -FilePath $BoreExe -ArgumentList "local 5565 --to bore.pub --port 33458" -RedirectStandardOutput $BoreLogFile -RedirectStandardError $BoreLogFile -WindowStyle Hidden -PassThru
        $proc.Id | Out-File -FilePath $BorePidFile -Encoding ascii
        Write-Host "    • Bore tunnel started on bore.pub:33458 (PID: $($proc.Id))" -ForegroundColor Green
    }

    # 3. Autonomous PC Agent Event Loop
    $agentProc = Test-ProcessAlive $AgentPidFile
    if ($agentProc) {
        Write-Host "    • PCAgent autonomous loop already running (PID: $($agentProc.Id))" -ForegroundColor Yellow
    } else {
        $agentScript = Join-Path $ScriptDir "pc_agent.py"
        $proc = Start-Process -FilePath $PythonExe -ArgumentList "-u", "`"$agentScript`"", "--loop-only" -RedirectStandardOutput $AgentLogFile -RedirectStandardError $AgentLogFile -WindowStyle Hidden -PassThru
        $proc.Id | Out-File -FilePath $AgentPidFile -Encoding ascii
        Write-Host "    • PCAgent autonomous loop started (PID: $($proc.Id))" -ForegroundColor Green
    }

    Write-Host ">>> ✅ OmniSwarm Hub is fully active and running 24/7 in background." -ForegroundColor Green
}

function Stop-Hub {
    Write-Host ">>> Stopping OmniSwarm Hub Services..." -ForegroundColor Yellow

    foreach ($pair in @(
        @{ File=$AgentPidFile; Name="PCAgent Loop" },
        @{ File=$BorePidFile; Name="Bore Tunnel" },
        @{ File=$HubPidFile; Name="OmniOS Kernel" }
    )) {
        $proc = Test-ProcessAlive $pair.File
        if ($proc) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "    • Stopped $($pair.Name) (PID: $($proc.Id))" -ForegroundColor Green
        }
        if (Test-Path $pair.File) { Remove-Item $pair.File -Force -ErrorAction SilentlyContinue }
    }
    Write-Host ">>> ✅ All Hub services stopped." -ForegroundColor Green
}

function Get-HubStatus {
    Write-Host "=== OmniSwarm Hub 24/7 Status ===" -ForegroundColor Cyan
    $hubProc = Test-ProcessAlive $HubPidFile
    $boreProc = Test-ProcessAlive $BorePidFile
    $agentProc = Test-ProcessAlive $AgentPidFile

    if ($hubProc) {
        Write-Host "  • OmniOS Kernel : 🟢 RUNNING (PID: $($hubProc.Id), Port: 5565)" -ForegroundColor Green
    } else {
        Write-Host "  • OmniOS Kernel : 🔴 STOPPED" -ForegroundColor Red
    }

    if ($boreProc) {
        Write-Host "  • Bore Tunnel   : 🟢 RUNNING (PID: $($boreProc.Id), Relay: bore.pub:33458)" -ForegroundColor Green
    } else {
        Write-Host "  • Bore Tunnel   : 🔴 STOPPED" -ForegroundColor Red
    }

    if ($agentProc) {
        Write-Host "  • PCAgent Loop  : 🟢 RUNNING (PID: $($agentProc.Id))" -ForegroundColor Green
    } else {
        Write-Host "  • PCAgent Loop  : 🔴 STOPPED" -ForegroundColor Red
    }
}

switch ($Action) {
    "start"   { Start-Hub }
    "stop"    { Stop-Hub }
    "status"  { Get-HubStatus }
    "restart" { Stop-Hub; Start-Sleep -Seconds 1; Start-Hub }
}
