<#
.SYNOPSIS
    OmniSwarm-OS Universal Turnkey Installer for Windows 10/11.
.DESCRIPTION
    Provisions isolated virtual environment, installs dependencies,
    whitelists firewall ports, configures mesh role, and verifies system health.
.PARAMETER Role
    "Hub" (daemon server) or "Edge" (client agent). Defaults to "Hub".
.PARAMETER HubHost
    Target Hub IP or domain. Defaults to "127.0.0.1" for Hub, "bore.pub" for Edge.
.PARAMETER HubPort
    Target Hub RPC port. Defaults to 5565 for Hub, 33458 for Edge.
#>
param(
    [ValidateSet("Hub", "Edge")]
    [string]$Role = "Hub",
    
    [string]$HubHost = "",
    [int]$HubPort = 0,
    [string]$NodeId = "WindowsNode-$env:COMPUTERNAME",
    [switch]$SkipFirewall = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if ([string]::IsNullOrEmpty($HubHost)) {
    if ($Role -eq "Hub") { $HubHost = "127.0.0.1" } else { $HubHost = "bore.pub" }
}
if ($HubPort -eq 0) {
    if ($Role -eq "Hub") { $HubPort = 5565 } else { $HubPort = 33458 }
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "       OmniSwarm-OS Universal Turnkey Windows Installer              " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Target Platform : Windows (PowerShell)"
Write-Host "Assigned Role   : $Role"
Write-Host "Target Hub      : ${HubHost}:${HubPort}"
Write-Host "Node ID         : $NodeId"
Write-Host "======================================================================"

# 1. Verify Python availability
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python 3 is required but not found in PATH. Please install Python 3.10+ and re-run."
    exit 1
}

# 2. Virtual Environment Provisioning
$venvPath = Join-Path $ScriptDir ".omnios_venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"

if (-not (Test-Path $venvPath)) {
    Write-Host ">>> [Venv] Creating isolated virtual environment at .omnios_venv..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# 3. Pip Requirements Installation
Write-Host ">>> [Pip] Installing OmniSwarm dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install -r (Join-Path $ScriptDir "requirements.txt") --quiet
& $venvPython -m pip install -e . --quiet

# 4. Submodule Check (ComputeRes)
$computeResPath = Join-Path $ScriptDir "ComputeRes"
if (-not (Test-Path $computeResPath)) {
    Write-Host ">>> [Submodule] Cloning ComputeRes (Execution Branch)..." -ForegroundColor Yellow
    git clone https://github.com/polymath-void/ComputeRes.git $computeResPath
}

# 5. Firewall Rule Configuration (for Hub roles)
if (-not $SkipFirewall -and $Role -eq "Hub") {
    Write-Host ">>> [Firewall] Ensuring Inbound TCP 5565/5566 are whitelisted..." -ForegroundColor Yellow
    try {
        $existing = Get-NetFirewallRule -DisplayName "OmniOS Raw Ports" -ErrorAction SilentlyContinue
        if (-not $existing) {
            New-NetFirewallRule -DisplayName "OmniOS Raw Ports" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5565,5566 -Profile Any -EdgeTraversalPolicy Allow | Out-Null
            Write-Host ">>> [Firewall] Rule created successfully." -ForegroundColor Green
        } else {
            Write-Host ">>> [Firewall] Rule already exists." -ForegroundColor Green
        }
    } catch {
        Write-Warning "Failed to set firewall rule (may require Run as Administrator): $_"
    }
}

# 6. Ensure bore.exe is downloaded for tunnel support
$boreExe = Join-Path $ScriptDir "bore.exe"
if (-not (Test-Path $boreExe)) {
    Write-Host ">>> [Tools] Downloading bore.exe TCP tunneling utility..." -ForegroundColor Yellow
    try {
        $boreZip = Join-Path $ScriptDir "bore_temp.zip"
        Invoke-WebRequest -Uri "https://github.com/ekzhang/bore/releases/download/v0.6.0/bore-v0.6.0-x86_64-pc-windows-msvc.zip" -OutFile $boreZip
        Expand-Archive -Path $boreZip -DestinationPath $ScriptDir -Force
        Remove-Item $boreZip -Force
        Write-Host ">>> [Tools] bore.exe downloaded successfully." -ForegroundColor Green
    } catch {
        Write-Warning "bore.exe download failed: $_"
    }
}

# 7. Write mesh_config.json
Write-Host ">>> [Config] Writing local mesh configuration..." -ForegroundColor Yellow
$configObj = [PSCustomObject]@{
    node_id         = $NodeId
    role            = $Role.ToLower()
    hub_host        = $HubHost
    rpc_port        = [int]$HubPort
    pub_port        = 5566
    auto_tunnel     = ($Role -eq "Hub")
    tunnel_provider = "bore"
}
$jsonContent = $configObj | ConvertTo-Json -Depth 3
[System.IO.File]::WriteAllText((Join-Path $ScriptDir "mesh_config.json"), $jsonContent, [System.Text.UTF8Encoding]::new($false))
Write-Host ">>> [Config] mesh_config.json created." -ForegroundColor Green

# 7.5 Provision Permanent Antigravity System Rules
Write-Host ">>> [System Rules] Provisioning permanent Antigravity system rules..." -ForegroundColor Yellow
& $venvPython (Join-Path $ScriptDir "scripts\inject_system_rules.py") --role $Role.ToLower() --workspace $ScriptDir

# 8. Run Self-Verification Diagnostics
Write-Host ">>> [Diagnostics] Running verification test suite..." -ForegroundColor Yellow
& $venvPython (Join-Path $ScriptDir "verify_install.py")

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "       OmniSwarm-OS Installation & Configuration Complete!            " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
if ($Role -eq "Hub") {
    Write-Host "To boot the Root Kernel Daemon:" -ForegroundColor Green
    Write-Host "  .omnios_venv\Scripts\python.exe omniswarm_py\omniswarm_daemon.py" -ForegroundColor White
} else {
    Write-Host "To execute a test skill against the Swarm:" -ForegroundColor Green
    Write-Host "  .omnios_venv\Scripts\python.exe test_sys_cpu_info.py" -ForegroundColor White
}
Write-Host "======================================================================" -ForegroundColor Cyan
