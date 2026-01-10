@echo off
setlocal

rem JAI Assistant startup script
rem - Sets working directory to the script location
rem - Avoids duplicate instances by checking if port 8001 is already listening
rem - Chooses the best available Python launcher (pyw/pythonw/py/python)

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "LOGFILE=%SCRIPT_DIR%start_jai.log"
echo [%DATE% %TIME%] Starting start_jai.cmd >> "%LOGFILE%"

rem Check if JAI (FastAPI on port 8001) is already running
set "JAI_PORT=8001"
rem Use a simple netstat check to avoid complex FOR parsing issues
cmd /c netstat -ano ^| findstr ":%JAI_PORT%" ^| findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo JAI appears to be running already on port %JAI_PORT%. Exiting. >> "%LOGFILE%"
  exit /b 0
)

rem Resolve Python interpreter (prefer project venv)
set "PYTHON_CMD="
set "VENV_PYW=%SCRIPT_DIR%venv\Scripts\pythonw.exe"
set "VENV_PY=%SCRIPT_DIR%venv\Scripts\python.exe"
if exist "%VENV_PYW%" set "PYTHON_CMD=%VENV_PYW%"
if not defined PYTHON_CMD if exist "%VENV_PY%" set "PYTHON_CMD=%VENV_PY%"
if not defined PYTHON_CMD where pyw >nul 2>&1 && set "PYTHON_CMD=pyw"
if not defined PYTHON_CMD where pythonw >nul 2>&1 && set "PYTHON_CMD=pythonw"
if not defined PYTHON_CMD where py >nul 2>&1 && set "PYTHON_CMD=py"
if not defined PYTHON_CMD where python >nul 2>&1 && set "PYTHON_CMD=python"
if defined PYTHON_CMD echo Using Python: %PYTHON_CMD% >> "%LOGFILE%"

if not defined PYTHON_CMD (
  echo No Python interpreter found (pyw/pythonw/py/python not in PATH or venv missing). >> "%LOGFILE%"
  echo Please install Python and ensure it is in PATH, or create a venv in the project. >> "%LOGFILE%"
  exit /b 1
)

rem Start JAI (pythonw avoids a console window)
echo [%DATE% %TIME%] Launching JAI... >> "%LOGFILE%"
start "" "%PYTHON_CMD%" "jai_assistant.py"
echo [%DATE% %TIME%] Launch command issued. Use netstat or the API to verify. >> "%LOGFILE%"
exit /b 0
