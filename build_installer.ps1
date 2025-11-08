Write-Host "Building JAI Voice Installer..."

# Path to Inno Setup compiler
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# Check if Inno Setup is installed
if (-not (Test-Path $innoPath)) {
    Write-Host "Error: Inno Setup is not installed in the default location."
    Write-Host "Please make sure Inno Setup is installed at: C:\Program Files (x86)\Inno Setup 6\"
    Write-Host "Or modify the `$innoPath in this script to point to your installation."
    pause
    exit 1
}

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Create the installer
Write-Host "Compiling installer..."
& "$innoPath" "$scriptDir\jai_voice_installer.iss"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild completed successfully!"
    Write-Host "Installer created as: $scriptDir\JAI_Voice_Installer.exe"
} else {
    Write-Host "`nError: Build failed with error code $LASTEXITCODE"
    exit $LASTEXITCODE
}

pause
