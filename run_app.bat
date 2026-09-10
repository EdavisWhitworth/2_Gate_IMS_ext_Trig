@echo off
setlocal

REM Get the folder where this batch file lives
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=%SCRIPT_DIR%requirements.txt"
set "APP_FILE=%SCRIPT_DIR%main.py"

REM Prefer py launcher on Windows, fall back to python if needed
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

REM Create the virtual environment if it does not exist
if not exist "%PYTHON_EXE%" (
    echo Creating virtual environment in %VENV_DIR%...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        echo Make sure Python 3 is installed and available via "py" or "python".
        exit /b 1
    )
)

REM Ensure pip is updated and dependencies are installed
echo Installing or updating dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to update pip.
    exit /b 1
)

"%PYTHON_EXE%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo Dependency installation failed.
    echo Check your internet connection and Python environment.
    exit /b 1
)

REM Launch the application immediately once dependencies are ready
echo Starting IMS Control...
"%PYTHON_EXE%" "%APP_FILE%"
if errorlevel 1 (
    echo The application exited with an error.
    exit /b %ERRORLEVEL%
)

endlocal
exit /b 0
