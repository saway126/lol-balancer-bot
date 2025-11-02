param(
    [string]$TaskName = 'MMRBot'
)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Scheduled task '$TaskName' removed."
