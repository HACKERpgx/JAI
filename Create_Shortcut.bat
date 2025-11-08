@echo off
setlocal

set "TARGET=%~dp0JAI_Launcher.bat"
set "SHORTCUT=%USERPROFILE%\Desktop\JAI Voice Assistant.lnk"
set "ICON=%%SystemRoot%%\System32\SHELL32.dll,71"
set "WORKDIR=%~dp0"

echo Creating shortcut...

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo sLinkFile = "%SHORTCUT%" >> "%TEMP%\create_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut.vbs"
echo oLink.TargetPath = "%TARGET%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.WorkingDirectory = "%WORKDIR%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Description = "JAI Voice Assistant" >> "%TEMP%\create_shortcut.vbs"
echo oLink.IconLocation = "%ICON%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.WindowStyle = 1 >> "%TEMP%\create_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_shortcut.vbs"

cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

echo.
echo Shortcut created on your desktop: "JAI Voice Assistant.lnk"
pause
