<#
  store_token.ps1
  Stores the Discord token into Windows Credential Manager via Python keyring.
  Usage: .\store_token.ps1
#>

$ErrorActionPreference = 'Stop'

Write-Host "Storing Discord token securely using Python keyring..."

# Prefer local venv python, fallback to system python
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path $python)) { $python = 'python' }

# Prompt for token as SecureString
$secure = Read-Host -AsSecureString 'Enter Discord token (stored securely)'
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))

# Use python -c to store token via keyring
$cmd = "import keyring, sys; keyring.set_password('mmr_bot','discord_token', sys.argv[1])"
& $python -c $cmd -- $plain
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to store token via keyring. Ensure package 'keyring' is installed in the active Python environment."
    exit $LASTEXITCODE
}

Write-Host "Token stored in Windows Credential Manager under service 'mmr_bot'."

# Clear plaintext variable
Remove-Variable plain -ErrorAction SilentlyContinue
