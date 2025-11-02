# Usage (run as Admin if needed):
# .\create_task.ps1 -TaskName "MMRBot" -ScriptPath "C:\Users\kks\Desktop\bot\run_bot.ps1"
param(
    [string]$TaskName = 'MMRBot',
    [string]$ScriptPath = "$PWD\run_bot.ps1"
)

$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force
Write-Host "Scheduled task '$TaskName' created to run $ScriptPath at logon."
