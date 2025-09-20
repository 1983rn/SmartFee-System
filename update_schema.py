#!/usr/bin/env python3
"""
Update database schema to add missing school configuration columns
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartfee.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def update_schema():
    """Add missing columns to school_configuration table"""
    with app.app_context():
        try:
            # Get database connection
            connection = db.engine.connect()
            
            # List of columns to add
            columns_to_add = [
                "ALTER TABLE school_configuration ADD COLUMN school_address TEXT",
                "ALTER TABLE school_configuration ADD COLUMN head_teacher_contact TEXT", 
                "ALTER TABLE school_configuration ADD COLUMN bursar_contact TEXT",
                "ALTER TABLE school_configuration ADD COLUMN school_email TEXT"
            ]
            
            for sql in columns_to_add:
                try:
                    connection.execute(sql)
                    print(f"Executed: {sql}")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        print(f"Column already exists: {sql}")
                    else:
                        print(f"Error: {e}")
            
            connection.close()
            print("Schema update completed!")
            return True
            
        except Exception as e:
            print(f"Failed to update schema: {e}")
            return False

if __name__ == "__main__":
    print("Updating database schema...")
    success = update_schema()
    if success:
        print("Database schema updated successfully!")
    else:
        print("Failed to update database schema!")
