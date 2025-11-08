# setup_windows_startup.ps1
# Sets up JAI to run automatically on Windows startup using Task Scheduler

param(
    [string]$Mode = "server",  # "server" or "voice"
    [switch]$Remove
)

$TaskName = "JAI_Assistant"
$ScriptPath = $PSScriptRoot
$PythonExe = Join-Path $ScriptPath "venv\Scripts\python.exe"
$PythonExeW = Join-Path $ScriptPath "venv\Scripts\pythonw.exe"

if ($Mode -eq "voice") {
    $TaskName = "JAI_Voice_Client"
    $PythonScript = Join-Path $ScriptPath "voice_client.py"
} else {
    $PythonScript = Join-Path $ScriptPath "jai_assistant.py"
}

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires administrator privileges" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again" -ForegroundColor Yellow
    exit 1
}

if ($Remove) {
    # Remove the scheduled task
    Write-Host "Removing scheduled task: $TaskName" -ForegroundColor Yellow
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✓ Task removed successfully" -ForegroundColor Green
    } else {
        Write-Host "Task not found: $TaskName" -ForegroundColor Yellow
    }
    exit 0
}

# Verify files exist
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python executable not found at: $PythonExe" -ForegroundColor Red
    Write-Host "Please ensure the virtual environment is set up correctly" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $PythonScript)) {
    Write-Host "ERROR: Script not found at: $PythonScript" -ForegroundColor Red
    exit 1
}

Write-Host "Setting up JAI for Windows startup..." -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor White
Write-Host "Script: $PythonScript" -ForegroundColor White
Write-Host ""

# Create the scheduled task (prefer pythonw.exe to run without a console)
$ExeToRun = if (Test-Path $PythonExeW) { $PythonExeW } else { $PythonExe }
$Action = New-ScheduledTaskAction -Execute $ExeToRun -Argument '"' + $PythonScript + '"' -WorkingDirectory $ScriptPath

# Trigger: At logon
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings (no backticks to avoid parsing issues)
$settingsParams = @{
    AllowStartIfOnBatteries = $true
    DontStopIfGoingOnBatteries = $true
    StartWhenAvailable = $true
    RestartCount = 3
    RestartInterval = (New-TimeSpan -Minutes 1)
}
$Settings = New-ScheduledTaskSettingsSet @settingsParams

# Principal (run with highest privileges)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Register the task
try {
    # Remove existing task if present
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "JAI Personal Assistant - Auto-start on login" -Force | Out-Null
    
    Write-Host "✓ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "JAI will now start automatically when you log in to Windows" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To manage the task:" -ForegroundColor White
    Write-Host "  - Open Task Scheduler (taskschd.msc)" -ForegroundColor Gray
    Write-Host "  - Look for task: $TaskName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To remove auto-start:" -ForegroundColor White
    Write-Host "  .\setup_windows_startup.ps1 -Remove" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "ERROR: Failed to create scheduled task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
