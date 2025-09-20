#!/usr/bin/env python3
"""
Initialize school configuration table with all required columns
"""

import sqlite3
import os
from datetime import datetime

def init_school_config():
    """Initialize school configuration table with all columns"""
    db_path = 'smartfee.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop existing table if it exists (backup data first if needed)
        cursor.execute("DROP TABLE IF EXISTS school_configuration_backup")
        cursor.execute("CREATE TABLE school_configuration_backup AS SELECT * FROM school_configuration WHERE 1=0")
        
        try:
            cursor.execute("INSERT INTO school_configuration_backup SELECT * FROM school_configuration")
            print("Backed up existing data")
        except:
            print("No existing data to backup")
        
        # Drop and recreate table with all columns
        cursor.execute("DROP TABLE IF EXISTS school_configuration")
        
        cursor.execute('''
            CREATE TABLE school_configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name VARCHAR(200) NOT NULL DEFAULT 'School Name',
                school_address TEXT,
                head_teacher_contact TEXT,
                bursar_contact TEXT,
                school_email TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_blocked BOOLEAN DEFAULT 0,
                subscription_status VARCHAR(20) DEFAULT 'trial',
                trial_start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                subscription_end_date DATETIME,
                subscription_type VARCHAR(20) DEFAULT 'trial',
                last_notification_sent DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Restore data if backup exists
        try:
            cursor.execute("SELECT COUNT(*) FROM school_configuration_backup")
            backup_count = cursor.fetchone()[0]
            if backup_count > 0:
                cursor.execute('''
                    INSERT INTO school_configuration 
                    (school_name, is_active, is_blocked, subscription_status, trial_start_date, 
                     subscription_end_date, subscription_type, last_notification_sent, created_at, updated_at)
                    SELECT school_name, is_active, is_blocked, subscription_status, trial_start_date,
                           subscription_end_date, subscription_type, last_notification_sent, created_at, updated_at
                    FROM school_configuration_backup
                ''')
                print("Restored existing data")
        except Exception as e:
            print(f"Could not restore backup data: {e}")
        
        # Check if there are any records
        cursor.execute("SELECT COUNT(*) FROM school_configuration")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert default configuration
            cursor.execute('''
                INSERT INTO school_configuration 
                (school_name, is_active, subscription_status, subscription_type, trial_start_date)
                VALUES (?, ?, ?, ?, ?)
            ''', ('SmartFee Revenue Collection System', True, 'trial', 'trial', datetime.utcnow()))
            print("Created default configuration")
        
        # Clean up backup table
        cursor.execute("DROP TABLE IF EXISTS school_configuration_backup")
        
        conn.commit()
        
        # Verify the table structure
        cursor.execute("PRAGMA table_info(school_configuration)")
        columns = cursor.fetchall()
        print("Table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        conn.close()
        print("School configuration table initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing school configuration: {e}")
        return False

if __name__ == "__main__":
    init_school_config()