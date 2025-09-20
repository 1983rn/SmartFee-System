@echo off
set PYTHONHOME=
set PYTHONPATH=
set VENV_PATH=%~dp0.venv-1

if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo Creating new virtual environment...
    C:\Users\NANJATI~1\AppData\Local\Programs\Python\Python312\python.exe -m venv "%VENV_PATH%"
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Installing dependencies...
"%VENV_PATH%\Scripts\pip.exe" install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

echo Starting application...
"%VENV_PATH%\Scripts\python.exe" app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application failed to start. Press any key to exit.
    pause >nul
    exit /b 1
)
