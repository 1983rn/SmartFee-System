#!/usr/bin/env python3
import sqlite3
import os

def check_database():
    db_path = 'smartfee.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Available tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if school_configuration table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%school%'")
        school_tables = cursor.fetchall()
        print(f"\nSchool-related tables: {school_tables}")
        
        # If school_configuration exists, show its structure
        for table in school_tables:
            table_name = table[0]
            print(f"\nStructure of {table_name}:")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_database()
