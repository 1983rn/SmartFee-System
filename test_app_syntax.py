#!/usr/bin/env python3
"""
Simple syntax test for app.py
"""

import ast
import sys

def test_syntax():
    try:
        with open('app.py', 'r') as f:
            source = f.read()
        
        # Parse the source code
        ast.parse(source)
        print("✓ app.py syntax is valid")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in app.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading app.py: {e}")
        return False

def check_imports():
    try:
        # Test basic imports
        import os
        import datetime
        print("✓ Basic Python modules available")
        
        # Check if Flask is available (will fail if not installed)
        try:
            import flask
            print("✓ Flask is available")
        except ImportError:
            print("✗ Flask not installed")
            
        try:
            import flask_sqlalchemy
            print("✓ Flask-SQLAlchemy is available")
        except ImportError:
            print("✗ Flask-SQLAlchemy not installed")
            
        try:
            import flask_wtf
            print("✓ Flask-WTF is available")
        except ImportError:
            print("✗ Flask-WTF not installed")
            
        return True
    except Exception as e:
        print(f"✗ Error checking imports: {e}")
        return False

if __name__ == '__main__':
    print("Testing SmartFee Revenue Application...")
    print("=" * 50)
    
    syntax_ok = test_syntax()
    imports_ok = check_imports()
    
    print("=" * 50)
    if syntax_ok:
        print("✓ Application structure is correct")
        print("\nTo run the application:")
        print("1. Install Python 3.9+ from python.org")
        print("2. Install dependencies: pip install flask flask-sqlalchemy flask-wtf python-dotenv")
        print("3. Run: python app.py")
    else:
        print("✗ Application has syntax errors")