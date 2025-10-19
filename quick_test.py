#!/usr/bin/env python3
"""
Quick diagnostic test for SmartFee system
"""

import sys
import os

def test_basic_functionality():
    """Test basic app functionality"""
    try:
        print("🔍 Testing SmartFee System...")
        
        # Test imports
        print("1. Testing imports...")
        from app import app, db
        print("   ✓ App imported successfully")
        
        # Test database
        print("2. Testing database...")
        with app.app_context():
            db.create_all()
            print("   ✓ Database tables created/verified")
        
        # Test basic route
        print("3. Testing basic functionality...")
        with app.test_client() as client:
            response = client.get('/')
            print(f"   ✓ Home route responds with status: {response.status_code}")
        
        print("\n✅ BASIC TESTS PASSED - Application appears functional")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR DETECTED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("SmartFee Quick Diagnostic Test")
    print("=" * 50)
    
    if test_basic_functionality():
        print("\n🚀 Try running: python app.py")
        print("   Or: python run_app.py")
        print("   Then access: http://localhost:5000")
    else:
        print("\n🔧 Issues detected. Please check the error above.")
    
    print("=" * 50)