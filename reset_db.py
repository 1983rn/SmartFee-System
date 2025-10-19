#!/usr/bin/env python3
import os
import shutil

# Remove corrupted database
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'smartfee.db')

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Removed corrupted database: {db_path}")

print("Database reset complete. Run the application to create a fresh database.")