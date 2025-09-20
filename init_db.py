#!/usr/bin/env python3
"""
Database initialization script
"""

from app import app, db

def init_database():
    """Initialize the database with all tables"""
    try:
        with app.app_context():
            # Drop all tables and recreate them
            db.drop_all()
            db.create_all()
            print("Database initialized successfully!")
            print("All tables created with correct schema.")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    init_database()