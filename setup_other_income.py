#!/usr/bin/env python3
"""
Simple setup script to ensure other_income table exists and is properly configured
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_other_income():
    """Setup other_income table"""
    try:
        # Import after adding to path
        from app import app, db, OtherIncome
        
        with app.app_context():
            print("Setting up other_income table...")
            
            # Create all tables (this is safe - won't overwrite existing)
            db.create_all()
            
            # Test the OtherIncome model
            count = db.session.query(OtherIncome).count()
            print(f"✓ other_income table is working. Current records: {count}")
            
            # Show table structure using raw SQL
            from sqlalchemy import text
            result = db.session.execute(text("PRAGMA table_info(other_income)"))
            columns = result.fetchall()
            
            print("Table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            return True
            
    except Exception as e:
        print(f"Setup error: {e}")
        return False

if __name__ == '__main__':
    print("Setting up other_income table...")
    success = setup_other_income()
    if success:
        print("\\n✓ Setup completed successfully!")
        print("The other_income table is now ready for use.")
    else:
        print("\\n✗ Setup failed!")
        print("Please check the error messages above.")