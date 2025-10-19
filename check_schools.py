#!/usr/bin/env python3
"""
Quick script to check schools in the database
"""
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'smartfee.db')

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if school_configuration table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='school_configuration'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("school_configuration table does not exist!")
        # Show all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Available tables:", [table[0] for table in tables])
    else:
        print("school_configuration table exists")
        
        # Get table schema
        cursor.execute("PRAGMA table_info(school_configuration)")
        columns = cursor.fetchall()
        print("\nTable schema:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Count schools
        cursor.execute("SELECT COUNT(*) FROM school_configuration")
        count = cursor.fetchone()[0]
        print(f"\nTotal schools in database: {count}")
        
        if count > 0:
            # Show all schools
            cursor.execute("SELECT id, school_name, is_active, subscription_status, created_at FROM school_configuration")
            schools = cursor.fetchall()
            print("\nSchools:")
            for school in schools:
                print(f"  ID: {school[0]}, Name: {school[1]}, Active: {school[2]}, Status: {school[3]}, Created: {school[4]}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")