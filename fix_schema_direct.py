#!/usr/bin/env python3
import sqlite3
import os

def fix_schema():
    db_path = 'smartfee.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== Adding missing school_id columns ===")
        
        # Tables that need school_id column
        tables_to_update = [
            'student',
            'income', 
            'expenditure',
            'receipt',
            'other_income',
            'budget',
            'fund_configuration'
        ]
        
        for table_name in tables_to_update:
            try:
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    print(f"Table {table_name} does not exist, skipping...")
                    continue
                
                # Check if school_id column exists
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = [row[1] for row in cursor.fetchall()]
                
                if 'school_id' not in existing_columns:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN school_id INTEGER"
                    cursor.execute(sql)
                    print(f"Added school_id column to {table_name}")
                else:
                    print(f"school_id column already exists in {table_name}")
                    
            except sqlite3.Error as e:
                print(f"Error updating {table_name}: {e}")
        
        print("\n=== Adding encryption_key column to school_configuration ===")
        
        # Add encryption_key to school_configuration
        try:
            cursor.execute("PRAGMA table_info(school_configuration)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            if 'encryption_key' not in existing_columns:
                cursor.execute("ALTER TABLE school_configuration ADD COLUMN encryption_key TEXT")
                print("Added encryption_key column to school_configuration")
            else:
                print("encryption_key column already exists in school_configuration")
                
        except sqlite3.Error as e:
            print(f"Error adding encryption_key: {e}")
        
        conn.commit()
        print("\n=== Schema update completed ===")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Fixing database schema...")
    if fix_schema():
        print("Schema fixed successfully!")
    else:
        print("Failed to fix schema!")
