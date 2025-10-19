#!/usr/bin/env python3
"""
Test script for SmartFee Revenue Collection System
Tests virtual environment setup and basic application functionality
"""

import sys
import os
import subprocess
import importlib.util

def test_virtual_environment():
    """Test if we're running in the correct virtual environment"""
    print("="*50)
    print("VIRTUAL ENVIRONMENT TEST")
    print("="*50)
    
    # Check Python executable path
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Running in virtual environment")
        return True
    else:
        print("✗ NOT running in virtual environment")
        return False

def test_required_packages():
    """Test if all required packages are installed"""
    print("\n" + "="*50)
    print("PACKAGE INSTALLATION TEST")
    print("="*50)
    
    required_packages = [
        'flask',
        'flask_sqlalchemy', 
        'flask_wtf',
        'wtforms'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            spec = importlib.util.find_spec(package)
            if spec is not None:
                print(f"✓ {package} - installed")
            else:
                print(f"✗ {package} - NOT FOUND")
                missing_packages.append(package)
        except ImportError:
            print(f"✗ {package} - IMPORT ERROR")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def test_app_imports():
    """Test if the main application can import successfully"""
    print("\n" + "="*50)
    print("APPLICATION IMPORT TEST")
    print("="*50)
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Try importing Flask components
        from flask import Flask
        print("✓ Flask imported successfully")
        
        from flask_sqlalchemy import SQLAlchemy
        print("✓ Flask-SQLAlchemy imported successfully")
        
        from flask_wtf import FlaskForm
        print("✓ Flask-WTF imported successfully")
        
        print("✓ All core imports successful")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    print("\n" + "="*50)
    print("DATABASE CONNECTION TEST")
    print("="*50)
    
    try:
        # Check if database file exists
        db_path = os.path.join('instance', 'smartfee.db')
        if os.path.exists(db_path):
            print(f"✓ Database file found: {db_path}")
            print(f"  File size: {os.path.getsize(db_path)} bytes")
            return True
        else:
            print(f"✗ Database file not found: {db_path}")
            return False
            
    except Exception as e:
        print(f"✗ Database test error: {e}")
        return False

def run_quick_app_test():
    """Run a quick test of the Flask application"""
    print("\n" + "="*50)
    print("FLASK APPLICATION TEST")
    print("="*50)
    
    try:
        # Import the app
        from app import app, db
        
        # Test app configuration
        print(f"✓ App imported successfully")
        print(f"  Debug mode: {app.debug}")
        print(f"  Secret key configured: {'SECRET_KEY' in app.config}")
        
        # Test database models
        with app.app_context():
            # Try to create tables
            db.create_all()
            print("✓ Database tables created/verified")
            
            # Test basic query
            from app import User
            user_count = User.query.count()
            print(f"✓ Database query successful - {user_count} users found")
        
        return True
        
    except Exception as e:
        print(f"✗ Flask app test error: {e}")
        return False

def main():
    """Run all tests"""
    print("SmartFee Revenue System - Virtual Environment Test")
    print("Testing Date:", __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Run tests
    venv_ok = test_virtual_environment()
    packages_ok, missing = test_required_packages()
    imports_ok = test_app_imports()
    db_ok = test_database_connection()
    app_ok = run_quick_app_test()
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    tests = [
        ("Virtual Environment", venv_ok),
        ("Required Packages", packages_ok),
        ("Application Imports", imports_ok),
        ("Database Connection", db_ok),
        ("Flask Application", app_ok)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if not packages_ok and missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
    
    if passed == total:
        print("\n🎉 All tests passed! Your application is ready to run.")
        print("Start the application with: python app.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()