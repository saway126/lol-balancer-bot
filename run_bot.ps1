# Headless runner for Discord MMR bot (NSSM/console safe)
$ErrorActionPreference = 'Stop'

# Activate venv if present
$venvActivate = Join-Path $PSScriptRoot '.venv\Scripts\Activate.ps1'
if (Test-Path $venvActivate) { . $venvActivate }

# Optional privileged intents flag. bot.py reads this.
if (-not $env:ENABLE_PRIVILEGED_INTENTS) {
    $env:ENABLE_PRIVILEGED_INTENTS = '0'
}

# Start the bot. Token is read from Windows Credential Manager via keyring
# or from DISCORD_TOKEN if you set it externally.
python (Join-Path $PSScriptRoot 'bot.py')