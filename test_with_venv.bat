@echo off
echo SmartFee Revenue System - Virtual Environment Testing
echo =====================================================

REM Change to the project directory
cd /d "c:\Users\NANJATI CDSS\Desktop\SOFTWARE\MASTERPRO\SmartFee_Revenue"

REM Activate virtual environment
echo Activating virtual environment...
call .venv-1\Scripts\activate.bat

REM Check if activation was successful
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated successfully!
echo.

REM Install/update requirements
echo Installing/updating requirements...
pip install -r requirements.txt

REM Run the test script
echo.
echo Running application tests...
python test_venv.py

echo.
echo Test completed. Press any key to continue...
pause

REM Keep the virtual environment active for manual testing
echo.
echo Virtual environment is still active.
echo You can now run: python app.py
echo Or type 'deactivate' to exit the virtual environment
cmd /k