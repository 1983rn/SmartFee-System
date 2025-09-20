@echo off
echo Starting deployment...

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate virtual environment and install dependencies
call .venv\Scripts\activate.bat

:: Install/update dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

:: Set environment to production
set FLASK_ENV=production

:: Initialize/upgrade database
echo Setting up database...
flask db upgrade

:: Stop any running Gunicorn processes
taskkill /F /IM gunicorn.exe /T 2>nul

:: Start Gunicorn
echo Starting Gunicorn...
start "" /B gunicorn -c gunicorn_config.py wsgi:app > gunicorn.log 2>&1

echo Deployment complete!
echo Application should be running on http://localhost:5000
echo Check gunicorn.log for any errors

pause
