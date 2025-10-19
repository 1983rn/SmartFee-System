#!/usr/bin/env python3
"""
Simple test script for SmartFee application without Unicode characters
"""

import sys
import traceback

def test_imports():
    """Test all required imports"""
    try:
        print("Testing imports...")
        from flask import Flask
        print("OK - Flask imported")
        
        from flask_sqlalchemy import SQLAlchemy
        print("OK - SQLAlchemy imported")
        
        from flask_wtf.csrf import CSRFProtect
        print("OK - CSRF imported")
        
        from datetime import datetime, timedelta
        print("OK - datetime imported")
        
        from functools import wraps
        print("OK - functools imported")
        
        import os
        print("OK - os imported")
        
        from dotenv import load_dotenv
        print("OK - dotenv imported")
        
        print("All imports successful!")
        return True
        
    except Exception as e:
        print(f"Import error: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test app creation and database setup"""
    try:
        print("\nTesting app creation...")
        from app import app, db
        print("OK - App and db imported")
        
        with app.app_context():
            print("OK - App context created")
            # Test database connection
            db.create_all()
            print("OK - Database tables created")
            
        print("App creation successful!")
        return True
        
    except Exception as e:
        print(f"App creation error: {e}")
        traceback.print_exc()
        return False

def test_models():
    """Test database models"""
    try:
        print("\nTesting models...")
        from app import Student, User, SchoolConfiguration, FundConfiguration
        print("OK - All models imported")
        return True
        
    except Exception as e:
        print(f"Model error: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("SmartFee Application Test")
    print("=" * 40)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test app creation
    if success and not test_app_creation():
        success = False
    
    # Test models
    if success and not test_models():
        success = False
    
    if success:
        print("\n" + "=" * 40)
        print("SUCCESS - ALL TESTS PASSED!")
        print("The application should be ready to run.")
        print("Try: python app.py")
    else:
        print("\n" + "=" * 40)
        print("FAILED - TESTS FAILED!")
        print("Please fix the errors above before running the application.")
    
    print("=" * 40)