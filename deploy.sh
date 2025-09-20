#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting deployment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # Unix/Linux/Mac
    source .venv/bin/activate
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set environment to production
export FLASK_ENV=production

# Initialize/upgrade database
echo "💾 Setting up database..."
flask db upgrade

# Collect static files (if any)
echo "📁 Collecting static files..."
# Add any collectstatic commands if needed

# Restart Gunicorn
echo "🔄 Restarting Gunicorn..."
pkill -f gunicorn || true
nohup gunicorn -c gunicorn_config.py wsgi:app > gunicorn.log 2>&1 &

echo "✅ Deployment complete!"
echo "🌐 Application should be running on http://localhost:5000"
echo "📄 Check gunicorn.log for any errors"
