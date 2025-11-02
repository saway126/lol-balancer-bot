# install_nssm_service.ps1
# Installs an NSSM service that runs the run_bot.ps1 wrapper (so token can be provided via keyring)
# Usage (Admin PowerShell): .\install_nssm_service.ps1

$NSSM = "E:\\Download\\nssm-2.24\\win64\\nssm.exe"
$ServiceName = "MMRBot"
$WorkingDir = $PSScriptRoot
$PowershellPath = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$Wrapper = Join-Path $WorkingDir "run_bot.ps1"

if (!(Test-Path $NSSM)) {
    $candidate = @(
        "C:\\ProgramData\\chocolatey\\bin\\nssm.exe",
        "C:\\ProgramData\\chocolatey\\lib\\nssm\\tools\\nssm.exe",
        "C:\\Program Files\\nssm\\win64\\nssm.exe",
        "C:\\tools\\nssm\\nssm.exe"
    )
    $found = $false
    foreach ($p in $candidate) { if (Test-Path $p) { $NSSM = $p; $found = $true; break } }
    if (-not $found) {
        $cmd = Get-Command nssm -ErrorAction SilentlyContinue
        if ($cmd) { $NSSM = $cmd.Source; $found = $true }
    }
    if (-not $found) {
        Write-Error "nssm.exe not found. Install with: choco install nssm -y, or place it at C:\\tools\\nssm\\nssm.exe"
        exit 1
    }
}
if (!(Test-Path $Wrapper)) {
    Write-Error "run_bot.ps1 not found at $Wrapper. Ensure run_bot.ps1 exists in the project root."
    exit 1
}

# Install service via NSSM CLI
Write-Host "Installing NSSM service '$ServiceName'..."
& $NSSM install $ServiceName $PowershellPath -NoProfile -ExecutionPolicy Bypass -File $Wrapper
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install service via NSSM (exit $LASTEXITCODE)."
    exit $LASTEXITCODE
}

# Set working directory
& $NSSM set $ServiceName AppDirectory $WorkingDir
# Optionally configure stdout/stderr output files
$logdir = Join-Path $WorkingDir "logs"
if (!(Test-Path $logdir)) { New-Item -ItemType Directory -Path $logdir | Out-Null }
& $NSSM set $ServiceName AppStdout (Join-Path $logdir "out.log")
& $NSSM set $ServiceName AppStderr (Join-Path $logdir "err.log")

# Auto-start on boot and auto-restart on unexpected exit
& $NSSM set $ServiceName Start SERVICE_AUTO_START
& $NSSM set $ServiceName AppExit Default Restart
& $NSSM set $ServiceName AppThrottle 1500

Write-Host "Service '$ServiceName' installed. Start it with:`n  & $NSSM start $ServiceName"

# E:\Download\nssm-2.24\win64\nssm.exe start MMRBot
