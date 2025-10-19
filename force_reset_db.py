#!/usr/bin/env python3
import os
import time

# Database path
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'smartfee.db')

print("Attempting to remove corrupted database...")

if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Successfully removed: {db_path}")
    except PermissionError:
        print("Database is locked. Please:")
        print("1. Close any running Flask applications")
        print("2. Close any database browsers/tools")
        print("3. Run this script again")
        exit(1)
else:
    print("Database file not found - already removed or doesn't exist")

print("Database reset complete. Run the application to create a fresh database.")