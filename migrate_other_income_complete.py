#!/usr/bin/env python3
"""
Complete migration for OtherIncome table with school_id support
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtherIncome, SchoolConfiguration

def migrate_other_income_complete():
    """Migrate other_income table to include school_id and ensure proper structure"""
    
    db_path = os.path.join('instance', 'smartfee.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        with app.app_context():
            # Connect directly to SQLite
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='other_income'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                print("Creating other_income table from scratch...")
                
                # Create the table using SQLAlchemy
                OtherIncome.__table__.create(db.engine, checkfirst=True)
                db.session.commit()
                
                print("✓ other_income table created successfully")
                
            else:
                print("other_income table exists, checking structure...")
                
                # Get current table structure
                cursor.execute("PRAGMA table_info(other_income)")
                columns = {col[1]: col[2] for col in cursor.fetchall()}
                print(f"Current columns: {list(columns.keys())}")
                
                # Check if school_id column exists
                if 'school_id' not in columns:
                    print("Adding school_id column...")
                    
                    # Add school_id column
                    cursor.execute("ALTER TABLE other_income ADD COLUMN school_id INTEGER")
                    
                    # Get the first school ID to use as default
                    cursor.execute("SELECT id FROM school_configuration WHERE is_active = 1 LIMIT 1")
                    default_school = cursor.fetchone()
                    default_school_id = default_school[0] if default_school else 1
                    
                    # Update existing records with default school_id
                    cursor.execute("UPDATE other_income SET school_id = ? WHERE school_id IS NULL", (default_school_id,))\n                    
                    print(f"✓ Added school_id column and updated {cursor.rowcount} existing records")
                
                # Check other required columns
                required_columns = {
                    'date': 'DATE',
                    'customer_name': 'VARCHAR(200)',
                    'income_type': 'VARCHAR(100)',
                    'total_charge': 'FLOAT',
                    'amount_paid': 'FLOAT',
                    'balance': 'FLOAT',
                    'created_at': 'DATETIME'
                }
                
                missing_columns = []
                for col_name, col_type in required_columns.items():
                    if col_name not in columns:
                        missing_columns.append((col_name, col_type))
                
                if missing_columns:
                    print(f"Adding missing columns: {[col[0] for col in missing_columns]}")
                    for col_name, col_type in missing_columns:
                        try:
                            cursor.execute(f"ALTER TABLE other_income ADD COLUMN {col_name} {col_type}")
                            print(f"✓ Added column: {col_name}")
                        except sqlite3.Error as e:
                            print(f"Error adding column {col_name}: {e}")
                
                conn.commit()
            
            # Verify final structure
            cursor.execute("PRAGMA table_info(other_income)")
            final_columns = cursor.fetchall()
            print("\\nFinal table structure:")
            for col in final_columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM other_income")
            count = cursor.fetchone()[0]
            print(f"\\nTotal records in other_income: {count}")
            
            conn.close()
            
            # Test with SQLAlchemy
            with app.app_context():
                try:
                    test_count = db.session.query(OtherIncome).count()
                    print(f"✓ SQLAlchemy can access table: {test_count} records")
                    return True
                except Exception as e:
                    print(f"✗ SQLAlchemy error: {e}")
                    return False
            
    except Exception as e:
        print(f"Migration error: {e}")
        return False

if __name__ == '__main__':
    print("Starting complete other_income table migration...")
    success = migrate_other_income_complete()
    if success:
        print("\\n✓ Migration completed successfully!")
    else:
        print("\\n✗ Migration failed!")