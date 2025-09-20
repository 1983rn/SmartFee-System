#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🚀 Starting build process..."

# Set Python version
PYTHON_VERSION=${PYTHON_VERSION:-3.9.16}
echo "🐍 Using Python $PYTHON_VERSION"

# Render manages the virtual environment for us, so we don't need to create one
echo "🔧 Using Render's managed Python environment..."

# Upgrade pip and setuptools
echo "🛠️ Upgrading pip and setuptools..."
python -m pip install --upgrade pip setuptools wheel

# Install requirements
echo "📦 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "✨ Build process completed successfully!"