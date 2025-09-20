#!/usr/bin/env python3
"""
Migration script to add Boarding Fee functionality to the SmartFee system.
This script adds boarding fee fields to Student, FundConfiguration, and other relevant tables.
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'smartfee.db')

def migrate_database():
    """
    Add boarding fee columns to existing database tables
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("Starting Boarding Fee migration...")
        
        # First, check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Available tables: {tables}")
        
        # Add boarding fee columns to student table
        try:
            cursor.execute("ALTER TABLE student ADD COLUMN boarding_amount_paid REAL DEFAULT 0.0")
            print("Added boarding_amount_paid to student table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("boarding_amount_paid column already exists in student table")
            elif "no such table" in str(e):
                print("Error: student table does not exist")
                return False
            else:
                raise e
        
        try:
            cursor.execute("ALTER TABLE student ADD COLUMN boarding_required REAL DEFAULT 0.0")
            print("Added boarding_required to student table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("boarding_required column already exists in student table")
            else:
                raise e
        
        try:
            cursor.execute("ALTER TABLE student ADD COLUMN boarding_installments INTEGER DEFAULT 0")
            print("Added boarding_installments to student table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("boarding_installments column already exists in student table")
            else:
                raise e
        
        # Add boarding fee column to fund_configuration table
        try:
            cursor.execute("ALTER TABLE fund_configuration ADD COLUMN boarding_amount REAL DEFAULT 0.0")
            print("Added boarding_amount to fund_configuration table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("boarding_amount column already exists in fund_configuration table")
            elif "no such table" in str(e):
                print("Error: fund_configuration table does not exist")
                return False
            else:
                raise e
        
        # Update existing fund configurations to include boarding fee (set to 0 initially)
        cursor.execute("UPDATE fund_configuration SET boarding_amount = 0.0 WHERE boarding_amount IS NULL")
        print("Updated existing fund configurations with default boarding amount")
        
        # Update existing students to include boarding fee fields (set to 0 initially)
        cursor.execute("UPDATE student SET boarding_amount_paid = 0.0 WHERE boarding_amount_paid IS NULL")
        cursor.execute("UPDATE student SET boarding_required = 0.0 WHERE boarding_required IS NULL")
        cursor.execute("UPDATE student SET boarding_installments = 0 WHERE boarding_installments IS NULL")
        print("Updated existing students with default boarding fee values")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(student)")
        student_columns = [row[1] for row in cursor.fetchall()]
        print(f"Student table columns: {student_columns}")
        
        cursor.execute("PRAGMA table_info(fund_configuration)")
        fund_config_columns = [row[1] for row in cursor.fetchall()]
        print(f"Fund configuration table columns: {fund_config_columns}")
        print("✅ Boarding Fee migration completed successfully!")
        
        # Display summary
        cursor.execute("SELECT COUNT(*) FROM student")
        student_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM fund_configuration")
        config_count = cursor.fetchone()[0]
        
        print(f"\nMigration Summary:")
        print(f"- Updated {student_count} student records")
        print(f"- Updated {config_count} fund configuration records")
        print(f"- Migration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🎉 You can now restart the application to use Boarding Fee functionality!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
