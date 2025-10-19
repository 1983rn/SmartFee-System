#!/usr/bin/env python3
"""
Simple script to add missing columns to the existing database
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database():
    """Create a backup of the current database"""
    if os.path.exists('smartfee.db'):
        backup_name = f'smartfee_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('smartfee.db', backup_name)
        print(f"Database backed up to: {backup_name}")
        return backup_name
    return None

def fix_database():
    """
    Fix database issues by adding missing boarding fee columns
    """
    try:
        # Create backup first
        backup_file = backup_database()
        
        # Connect to database
        conn = sqlite3.connect('smartfee.db')
        cursor = conn.cursor()
        
        print("Starting database fix...")
        
        # Get current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Current tables: {tables}")
        
        if not tables:
            print("No tables found. Database needs to be initialized first.")
            # Initialize with Flask app models
            print("Initializing database with Flask models...")
            conn.close()
            
            # Import and initialize with Flask
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from app import app, db
            
            with app.app_context():
                db.create_all()
                print("Database initialized with all tables including boarding fee fields")
            
            return True
        
        # Check if we need to add boarding columns
        needs_migration = False
        
        if 'student' in tables:
            cursor.execute("PRAGMA table_info(student)")
            student_columns = [row[1] for row in cursor.fetchall()]
            if 'boarding_amount_paid' not in student_columns:
                needs_migration = True
                print("Student table needs boarding fee columns")
        
        if 'fund_configuration' in tables:
            cursor.execute("PRAGMA table_info(fund_configuration)")
            config_columns = [row[1] for row in cursor.fetchall()]
            if 'boarding_amount' not in config_columns:
                needs_migration = True
                print("Fund configuration table needs boarding amount column")
        
        if needs_migration:
            print("Performing database migration...")
            
            # Add missing columns to student table
            try:
                cursor.execute("ALTER TABLE student ADD COLUMN boarding_amount_paid REAL DEFAULT 0.0")
                print("Added boarding_amount_paid to student table")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e):
                    print(f"Error adding boarding_amount_paid: {e}")
            
            try:
                cursor.execute("ALTER TABLE student ADD COLUMN boarding_required REAL DEFAULT 0.0")
                print("Added boarding_required to student table")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e):
                    print(f"Error adding boarding_required: {e}")
            
            try:
                cursor.execute("ALTER TABLE student ADD COLUMN boarding_installments INTEGER DEFAULT 0")
                print("Added boarding_installments to student table")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e):
                    print(f"Error adding boarding_installments: {e}")
            
            # Add missing column to fund_configuration table
            try:
                cursor.execute("ALTER TABLE fund_configuration ADD COLUMN boarding_amount REAL DEFAULT 0.0")
                print("Added boarding_amount to fund_configuration table")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e):
                    print(f"Error adding boarding_amount: {e}")
            
            # Update existing records with default values
            cursor.execute("UPDATE student SET boarding_amount_paid = 0.0 WHERE boarding_amount_paid IS NULL")
            cursor.execute("UPDATE student SET boarding_required = 0.0 WHERE boarding_required IS NULL") 
            cursor.execute("UPDATE student SET boarding_installments = 0 WHERE boarding_installments IS NULL")
            cursor.execute("UPDATE fund_configuration SET boarding_amount = 0.0 WHERE boarding_amount IS NULL")
            
            conn.commit()
            print("Database migration completed successfully!")
        else:
            print("Database already has boarding fee columns")
        
        # Verify the final structure
        cursor.execute("PRAGMA table_info(student)")
        student_columns = [row[1] for row in cursor.fetchall()]
        print(f"Student table columns: {student_columns}")
        
        cursor.execute("PRAGMA table_info(fund_configuration)")
        config_columns = [row[1] for row in cursor.fetchall()]
        print(f"Fund configuration columns: {config_columns}")
        
        return True
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("\nDatabase fix completed successfully!")
        print("You can now restart the Flask application.")
    else:
        print("\nDatabase fix failed!")
        exit(1)