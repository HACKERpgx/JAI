@echo off
echo Building JAI Voice Installer...

:: Set path to Inno Setup compiler (default installation path)
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

:: Check if Inno Setup is installed
if not exist %INNO_PATH% (
    echo Error: Inno Setup is not installed in the default location.
    echo Please make sure Inno Setup is installed at: C:\Program Files (x86)\Inno Setup 6\
    echo Or modify the INNO_PATH in this script to point to your installation.
    pause
    exit /b 1
)

:: Create the installer
echo Compiling installer...
%INNO_PATH% "jai_voice_installer.iss"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Build completed successfully!
    echo Installer created as: JAI_Voice_Installer.exe
) else (
    echo.
    echo Error: Build failed with error code %ERRORLEVEL%
)

pause
