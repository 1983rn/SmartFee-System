#!/usr/bin/env python3
"""
Test script to identify issues with the SmartFee application
"""

import sys
import traceback

def test_imports():
    """Test all required imports"""
    try:
        print("Testing imports...")
        from flask import Flask
        print("✓ Flask imported")
        
        from flask_sqlalchemy import SQLAlchemy
        print("✓ SQLAlchemy imported")
        
        from flask_wtf.csrf import CSRFProtect
        print("✓ CSRF imported")
        
        from datetime import datetime, timedelta
        print("✓ datetime imported")
        
        from functools import wraps
        print("✓ functools imported")
        
        import os
        print("✓ os imported")
        
        from dotenv import load_dotenv
        print("✓ dotenv imported")
        
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
        print("✓ App and db imported")
        
        with app.app_context():
            print("✓ App context created")
            # Test database connection
            db.create_all()
            print("✓ Database tables created")
            
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
        from app import Student, Income, Receipt, FundConfiguration, SchoolConfiguration
        print("✓ All models imported")
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
        print("✓ ALL TESTS PASSED!")
        print("The application should be ready to run.")
        print("Try: python app.py")
    else:
        print("\n" + "=" * 40)
        print("✗ TESTS FAILED!")
        print("Please fix the errors above before running the application.")
    
    print("=" * 40)
