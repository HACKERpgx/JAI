@echo off
setlocal

:: Set the working directory to the script's location
cd /d "%~dp0"

:: Set David as the default voice
set TTS_VOICE=David

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.x from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if required packages are installed
python -c "import pyttsx3, pywin32, comtypes, pycaw" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required Python packages...
    pip install pyttsx3 pywin32 comtypes pycaw
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install required packages.
        echo Please run 'pip install pyttsx3 pywin32 comtypes pycaw' manually.
        pause
        exit /b 1
    )
)

:: Run the JAI Assistant
echo Starting JAI Voice Assistant...
python -c "import jai_assistant; jai_assistant.main()"

:: Keep the window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo JAI Voice Assistant closed with an error.
    echo Please check the error message above.
    pause
)

endlocal
