#!/usr/bin/env python3
"""
Script to create the other_income table if it doesn't exist
"""
import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import app, db, OtherIncome

def create_other_income_table():
    """Create the other_income table if it doesn't exist"""
    try:
        with app.app_context():
            # Check if table exists
            from sqlalchemy import text
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='other_income'"))
            table_exists = result.fetchone() is not None
            
            if table_exists:
                print("✓ other_income table already exists")
                
                # Check table structure
                result = db.session.execute(text("PRAGMA table_info(other_income)"))
                columns = result.fetchall()
                print("Current table structure:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
            else:
                print("Creating other_income table...")
                
                # Create the table
                OtherIncome.__table__.create(db.engine, checkfirst=True)
                db.session.commit()
                
                print("✓ other_income table created successfully")
                
                # Show the new table structure
                result = db.session.execute(text("PRAGMA table_info(other_income)"))
                columns = result.fetchall()
                print("New table structure:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            
            # Test the table by counting records
            count = db.session.query(OtherIncome).count()
            print(f"Current records in other_income table: {count}")
            
            return True
            
    except Exception as e:
        print(f"Error creating other_income table: {e}")
        return False

if __name__ == "__main__":
    print("Creating other_income table...")
    success = create_other_income_table()
    if success:
        print("✓ Operation completed successfully")
    else:
        print("✗ Operation failed")