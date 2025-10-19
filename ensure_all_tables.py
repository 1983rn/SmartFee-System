#!/usr/bin/env python3
"""
Script to ensure all database tables exist
"""
import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app and all models
from app import app, db, Student, Income, Expenditure, FundConfiguration, SchoolConfiguration, User, Subscription, NotificationLog, Receipt, OtherIncome, Budget, ProfessionalReceipt

def ensure_all_tables():
    """Ensure all database tables exist"""
    try:
        with app.app_context():
            print("Checking and creating database tables...")
            
            # Create all tables
            db.create_all()
            
            # List all tables to verify
            from sqlalchemy import text
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
            tables = result.fetchall()
            
            print("Available tables:")
            for table in tables:
                table_name = table[0]
                print(f"  ✓ {table_name}")
                
                # Count records in each table
                try:
                    count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = count_result.fetchone()[0]
                    print(f"    Records: {count}")
                except Exception as e:
                    print(f"    Error counting records: {e}")
            
            # Specifically check for other_income table
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='other_income'"))
            other_income_exists = result.fetchone() is not None
            
            if other_income_exists:
                print("\n✓ other_income table confirmed to exist")
                
                # Show structure
                result = db.session.execute(text("PRAGMA table_info(other_income)"))
                columns = result.fetchall()
                print("other_income table structure:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("\n✗ other_income table missing - this should not happen after db.create_all()")
            
            return True
            
    except Exception as e:
        print(f"Error ensuring tables: {e}")
        return False

if __name__ == "__main__":
    print("Ensuring all database tables exist...")
    success = ensure_all_tables()
    if success:
        print("\n✓ All tables verified/created successfully")
    else:
        print("\n✗ Operation failed")