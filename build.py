#!/usr/bin/env python3
"""
Build script for Render deployment.
This script initializes the database and creates necessary tables.
"""

import os
from app import app, db, create_default_school_and_admin, ensure_database_schema

def initialize_database():
    """Initialize database for production deployment."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("Ensuring database schema is up to date...")
        ensure_database_schema()
        
        print("Creating default school and admin user...")
        create_default_school_and_admin()
        
        print("Database initialization completed successfully!")

if __name__ == "__main__":
    initialize_database()