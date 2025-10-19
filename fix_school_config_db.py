#!/usr/bin/env python3
"""
Fix school configuration database schema
"""

import sqlite3
import os
from datetime import datetime

def fix_school_config_db():
    """Add missing columns to school_configuration table"""
    db_path = 'smartfee.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='school_configuration'")
        if not cursor.fetchone():
            print("SchoolConfiguration table not found!")
            conn.close()
            return False
        
        # Get current columns
        cursor.execute("PRAGMA table_info(school_configuration)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add missing columns
        new_columns = [
            'school_address',
            'head_teacher_contact', 
            'bursar_contact',
            'school_email'
        ]
        
        for column in new_columns:
            if column not in columns:
                try:
                    cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {column} TEXT")
                    print(f"Added column: {column}")
                except sqlite3.Error as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"Error adding {column}: {e}")
        
        conn.commit()
        
        # Verify columns were added
        cursor.execute("PRAGMA table_info(school_configuration)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
        # Test a simple query
        cursor.execute("SELECT COUNT(*) FROM school_configuration")
        count = cursor.fetchone()[0]
        print(f"Table has {count} records")
        
        conn.close()
        print("Database schema fixed successfully!")
        return True
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False

if __name__ == "__main__":
    print("Fixing school configuration database schema...")
    success = fix_school_config_db()
    if success:
        print("Schema fix completed!")
    else:
        print("Schema fix failed!")
