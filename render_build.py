#!/usr/bin/env python3
"""
Simple Python build script for Render deployment
This avoids shell script issues and uses Python directly
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    print("🚀 Starting Python build process...")
    
    # Upgrade pip and setuptools
    if not run_command("python -m pip install --upgrade pip setuptools wheel", 
                      "Upgrading pip and setuptools"):
        sys.exit(1)
    
    # Install requirements
    if not run_command("pip install --no-cache-dir -r requirements.txt", 
                      "Installing Python dependencies"):
        sys.exit(1)
    
    print("✨ Build process completed successfully!")

if __name__ == "__main__":
    main()
