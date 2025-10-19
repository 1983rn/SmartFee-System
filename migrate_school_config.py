#!/usr/bin/env python3
"""
Migration script to add new fields to SchoolConfiguration table
- school_address
- head_teacher_contact  
- bursar_contact
- school_email
"""

import sqlite3
import os
from datetime import datetime

def migrate_school_config():
    """Add new fields to SchoolConfiguration table"""
    db_path = 'smartfee.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        # Create backup
        backup_path = f'smartfee_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Created backup: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='school_configuration'")
        if not cursor.fetchone():
            print("SchoolConfiguration table not found!")
            return False
        
        # Get current table structure
        cursor.execute("PRAGMA table_info(school_configuration)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add new columns if they don't exist
        new_columns = [
            ('school_address', 'TEXT'),
            ('head_teacher_contact', 'TEXT'),
            ('bursar_contact', 'TEXT'),
            ('school_email', 'TEXT')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE school_configuration ADD COLUMN {column_name} {column_type}")
                    print(f"Added column: {column_name}")
                except sqlite3.Error as e:
                    print(f"Error adding column {column_name}: {e}")
        
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(school_configuration)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM school_configuration")
        count = cursor.fetchone()[0]
        print(f"SchoolConfiguration table has {count} records")
        
        conn.close()
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting SchoolConfiguration migration...")
    success = migrate_school_config()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
