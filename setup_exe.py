#!/usr/bin/env python3
"""
Setup script to create executable for SmartFee System
Uses PyInstaller to create a standalone Windows executable
"""

import os
import sys
import subprocess
import shutil

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed successfully")

def create_executable():
    """Create the executable using PyInstaller"""
    print("Creating executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Don't show console window
        "--name=SmartFeeSystem",  # Name of the executable
        "--icon=icon.ico",  # Icon file (if exists)
        "--add-data=templates;templates",  # Include templates folder
        "--add-data=static;static",  # Include static folder (if exists)
        "--hidden-import=flask_wtf.csrf",
        "--hidden-import=flask_sqlalchemy",
        "--hidden-import=dotenv",
        "app.py"
    ]
    
    # Remove icon parameter if icon doesn't exist
    if not os.path.exists("icon.ico"):
        cmd.remove("--icon=icon.ico")
    
    # Remove static folder parameter if it doesn't exist
    if not os.path.exists("static"):
        cmd.remove("--add-data=static;static")
    
    try:
        subprocess.check_call(cmd)
        print("✓ Executable created successfully!")
        
        # Move executable to current directory
        exe_path = os.path.join("dist", "SmartFeeSystem.exe")
        if os.path.exists(exe_path):
            shutil.move(exe_path, "SmartFeeSystem.exe")
            print("✓ Executable moved to current directory: SmartFeeSystem.exe")
        
        # Clean up build files
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("SmartFeeSystem.spec"):
            os.remove("SmartFeeSystem.spec")
        
        print("✓ Build files cleaned up")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating executable: {e}")
        return False
    
    return True

def create_installer():
    """Create a simple installer script"""
    installer_content = '''@echo off
echo SmartFee System Installer
echo ========================
echo.
echo This will install SmartFee System on your computer.
echo.
pause

REM Create installation directory
if not exist "C:\\SmartFeeSystem" mkdir "C:\\SmartFeeSystem"

REM Copy executable
copy "SmartFeeSystem.exe" "C:\\SmartFeeSystem\\"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\SmartFee System.lnk'); $Shortcut.TargetPath = 'C:\\SmartFeeSystem\\SmartFeeSystem.exe'; $Shortcut.Save()"

echo.
echo Installation completed!
echo You can now run SmartFee System from your desktop or from C:\\SmartFeeSystem\\
echo.
pause
'''
    
    with open("install_smartfee.bat", "w") as f:
        f.write(installer_content)
    
    print("✓ Installer script created: install_smartfee.bat")

def main():
    """Main function to create executable and installer"""
    print("SmartFee System - Executable Builder")
    print("====================================")
    print()
    
    # Check if we're on Windows
    if os.name != 'nt':
        print("❌ This script is designed for Windows only")
        return
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Create executable
    if create_executable():
        # Create installer
        create_installer()
        
        print()
        print("🎉 Build completed successfully!")
        print()
        print("Files created:")
        print("- SmartFeeSystem.exe (Main executable)")
        print("- install_smartfee.bat (Installer script)")
        print()
        print("To install on another computer:")
        print("1. Copy both files to the target computer")
        print("2. Run install_smartfee.bat as administrator")
        print("3. The system will be installed to C:\\SmartFeeSystem\\")
        print("4. A desktop shortcut will be created")
    else:
        print("❌ Build failed!")

if __name__ == "__main__":
    main() 