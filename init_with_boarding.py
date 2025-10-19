#!/usr/bin/env python3
"""
Initialize database with boarding fee support
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app and database
from app import app, db

def init_database():
    """Initialize database with all tables including boarding fee fields"""
    try:
        with app.app_context():
            print("Creating database tables...")
            
            # Create all tables
            db.create_all()
            
            print("Database initialized successfully!")
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Created tables: {tables}")
            
            # Check student table columns
            if 'student' in tables:
                student_columns = [col['name'] for col in inspector.get_columns('student')]
                print(f"Student table columns: {student_columns}")
                
                # Check if boarding columns exist
                boarding_cols = [col for col in student_columns if 'boarding' in col]
                if boarding_cols:
                    print(f"Boarding columns found: {boarding_cols}")
                else:
                    print("No boarding columns found in student table")
            
            # Check fund_configuration table columns
            if 'fund_configuration' in tables:
                config_columns = [col['name'] for col in inspector.get_columns('fund_configuration')]
                print(f"Fund configuration table columns: {config_columns}")
                
                # Check if boarding column exists
                if 'boarding_amount' in config_columns:
                    print("Boarding amount column found in fund_configuration table")
                else:
                    print("No boarding_amount column found in fund_configuration table")
            
            return True
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("✅ Database initialization completed successfully!")
    else:
        print("❌ Database initialization failed!")
        sys.exit(1)
