#!/usr/bin/env python3

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_other_income_table():
    """Test and create other_income table if needed"""
    try:
        # Import after adding to path
        from app import app, db, OtherIncome
        
        with app.app_context():
            print("Testing other_income table...")
            
            # Create all tables (this is safe - won't overwrite existing)
            db.create_all()
            print("✓ Database tables created/verified")
            
            # Test the OtherIncome model
            try:
                count = db.session.query(OtherIncome).count()
                print(f"✓ other_income table is working. Current records: {count}")
            except Exception as e:
                print(f"Error querying other_income table: {e}")
                # Try to create the table explicitly
                OtherIncome.__table__.create(db.engine, checkfirst=True)
                print("✓ other_income table created explicitly")
                count = db.session.query(OtherIncome).count()
                print(f"✓ other_income table is now working. Current records: {count}")
            
            # Show table structure using raw SQL
            from sqlalchemy import text
            try:
                result = db.session.execute(text("PRAGMA table_info(other_income)"))
                columns = result.fetchall()
                
                print("Table structure:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            except Exception as e:
                print(f"Could not get table info: {e}")
            
            return True
            
    except Exception as e:
        print(f"Setup error: {e}")
        return False

if __name__ == '__main__':
    print("Testing other_income table setup...")
    success = test_other_income_table()
    if success:
        print("\n✓ Test completed successfully!")
        print("The other_income table should now be working.")
    else:
        print("\n✗ Test failed!")
        print("Please check the error messages above.")