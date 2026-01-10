@echo off
title JAI Voice Assistant Setup

echo ================================================
echo  JAI Voice Assistant - Simple Installer
echo ================================================
echo.
echo This will install JAI Voice Assistant with David as the default voice.
echo.
pause

set INSTALL_DIR="%USERPROFILE%\JAI_Voice_Assistant"

:: Create installation directory
if not exist %INSTALL_DIR% (
    mkdir %INSTALL_DIR%
) else (
    echo Updating existing installation...
)

:: Copy files
echo Copying files...
copy "%~dp0jai_assistant.py" %INSTALL_DIR%\
copy "%~dp0jai_controls.py" %INSTALL_DIR%\
copy "%~dp0jai_media.py" %INSTALL_DIR%\
copy "%~dp0jai_calendar.py" %INSTALL_DIR%\
copy "%~dp0requirements.txt" %INSTALL_DIR%\

:: Create a launcher file
echo @echo off > "%INSTALL_DIR%\Run_JAI.bat"
echo set TTS_VOICE=David >> "%INSTALL_DIR%\Run_JAI.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%\Run_JAI.bat"
echo python jai_assistant.py >> "%INSTALL_DIR%\Run_JAI.bat"
echo pause >> "%INSTALL_DIR%\Run_JAI.bat"

:: Create desktop shortcut
echo Creating desktop shortcut...
set SCRIPT="%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\JAI Voice Assistant.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%INSTALL_DIR%\Run_JAI.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> %SCRIPT%
echo oLink.Description = "JAI Voice Assistant" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo ================================================
echo  Installation Complete!
echo ================================================
echo.
echo JAI Voice Assistant has been installed to %INSTALL_DIR%
echo.
echo To run JAI Voice Assistant:
echo 1. Double-click the desktop shortcut
echo 2. Or run %INSTALL_DIR%\Run_JAI.bat
echo.
echo Note: Make sure Python 3.8 or later is installed and
      added to your system PATH.
echo.
pause
