#!/usr/bin/env python3
"""
Migration script to add deposit_slip_ref column to Student table
"""

import sqlite3
import os
from datetime import datetime

def add_deposit_slip_ref_column():
    """Add deposit_slip_ref column to Student table if it doesn't exist"""
    
    # Database path
    db_path = os.path.join('instance', 'smartfee.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(student)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'deposit_slip_ref' in columns:
            print("Column 'deposit_slip_ref' already exists in Student table")
            conn.close()
            return True
        
        # Add the column
        cursor.execute("ALTER TABLE student ADD COLUMN deposit_slip_ref TEXT")
        conn.commit()
        
        print("Successfully added 'deposit_slip_ref' column to Student table")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(student)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'deposit_slip_ref' in columns:
            print("Column addition verified successfully")
        else:
            print("Warning: Column addition could not be verified")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Adding deposit_slip_ref column to Student table...")
    success = add_deposit_slip_ref_column()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")