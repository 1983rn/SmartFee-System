@echo off
setlocal enabledelayedexpansion
echo ========================================
echo    Other Income Table Setup
echo ========================================
echo.

REM Check if setup script exists
if not exist "setup_other_income.py" (
    echo ERROR: setup_other_income.py not found!
    echo Please ensure you're running this from the correct directory.
    goto :error
)

REM Try different Python executables
set PYTHON_CMD=
set PYTHON_VERSION=

if exist ".venv-1\Scripts\python.exe" (
    set PYTHON_CMD=".venv-1\Scripts\python.exe"
    set PYTHON_VERSION=Virtual Environment
    echo [INFO] Using virtual environment Python...
) else if exist "python 3.13.7\Scripts\python.exe" (
    set PYTHON_CMD="python 3.13.7\Scripts\python.exe"
    set PYTHON_VERSION=Python 3.13.7
    echo [INFO] Using Python 3.13.7...
) else (
    set PYTHON_CMD=python
    set PYTHON_VERSION=System Python
    echo [INFO] Using system Python...
)

echo [INFO] Python Version: !PYTHON_VERSION!
echo [INFO] Executing setup script...
echo.

REM Execute the Python script and capture exit code
!PYTHON_CMD! setup_other_income.py
set EXIT_CODE=!ERRORLEVEL!

echo.
if !EXIT_CODE! equ 0 (
    echo [SUCCESS] Setup completed successfully!
    echo [INFO] The other_income table is now ready for use.
) else (
    echo [ERROR] Setup failed with exit code: !EXIT_CODE!
    echo [INFO] Please check the error messages above.
    goto :error
)

echo.
echo Press any key to continue...
pause > nul
goto :end

:error
echo.
echo [ERROR] Setup process encountered an error.
echo Press any key to exit...
pause > nul
exit /b 1

:end
exit /b 0