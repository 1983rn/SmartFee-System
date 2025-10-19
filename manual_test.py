#!/usr/bin/env python3
"""
Manual test script for SmartFee Revenue Collection System
Run this after the automated tests pass
"""

import os
import sys
from datetime import datetime

def test_app_startup():
    """Test if the app can start without errors"""
    print("Testing application startup...")
    
    try:
        # Import the app
        from app import app, db, User, DEFAULT_USERNAME, DEFAULT_PASSWORD
        
        print("✓ Application imported successfully")
        
        # Test app context
        with app.app_context():
            # Create tables
            db.create_all()
            print("✓ Database tables created")
            
            # Check default user
            user = User.query.filter_by(username=DEFAULT_USERNAME).first()
            if user:
                print(f"✓ Default user '{DEFAULT_USERNAME}' exists")
            else:
                print(f"ℹ Default user '{DEFAULT_USERNAME}' will be created on first run")
            
            # Test basic queries
            user_count = User.query.count()
            print(f"✓ Database operational - {user_count} users in system")
        
        return True
        
    except Exception as e:
        print(f"✗ Startup test failed: {e}")
        return False

def show_app_info():
    """Display application information"""
    try:
        from app import app, DEFAULT_USERNAME, DEFAULT_PASSWORD
        
        print("\n" + "="*50)
        print("APPLICATION INFORMATION")
        print("="*50)
        print(f"Application Name: SmartFee Revenue Collection System")
        print(f"Flask Debug Mode: {app.debug}")
        print(f"Default URL: http://127.0.0.1:5001")
        print(f"Default Username: {DEFAULT_USERNAME}")
        print(f"Default Password: {DEFAULT_PASSWORD}")
        print("="*50)
        
    except Exception as e:
        print(f"Could not load app info: {e}")

def main():
    """Run manual tests"""
    print("SmartFee Revenue System - Manual Test")
    print("Testing Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Test startup
    startup_ok = test_app_startup()
    
    # Show app info
    show_app_info()
    
    if startup_ok:
        print("\n🎉 Manual test passed!")
        print("\nTo start the application:")
        print("1. Make sure virtual environment is activated")
        print("2. Run: python app.py")
        print("3. Open browser to: http://127.0.0.1:5001")
        print("4. Login with the default credentials shown above")
    else:
        print("\n❌ Manual test failed!")
        print("Please check the error messages above.")
    
    return startup_ok

if __name__ == "__main__":
    main()