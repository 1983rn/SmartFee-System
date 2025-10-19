#!/usr/bin/env python3
"""
Database migration script for SmartFee System
Handles database schema updates and data migration
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migrate the database to the latest schema"""
    # Check both possible database locations
    db_paths = ['smartfee.db', 'instance/smartfee.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Database file not found. Creating new database...")
        return
    
    print(f"Found database at: {db_path}")
    print("Starting database migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if sex column exists in Student table
        cursor.execute("PRAGMA table_info(Student)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sex' not in columns:
            print("Adding 'sex' column to Student table...")
            cursor.execute("ALTER TABLE Student ADD COLUMN sex TEXT DEFAULT 'Male'")
            print("✓ Added 'sex' column")
        
        # Check if installment columns exist
        if 'pta_installments' not in columns:
            print("Adding 'pta_installments' column to Student table...")
            cursor.execute("ALTER TABLE Student ADD COLUMN pta_installments INTEGER DEFAULT 0")
            print("✓ Added 'pta_installments' column")
        
        if 'sdf_installments' not in columns:
            print("Adding 'sdf_installments' column to Student table...")
            cursor.execute("ALTER TABLE Student ADD COLUMN sdf_installments INTEGER DEFAULT 0")
            print("✓ Added 'sdf_installments' column")
        
        # Check if Receipt table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Receipt'")
        if not cursor.fetchone():
            print("Creating Receipt table...")
            cursor.execute("""
                CREATE TABLE Receipt (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_no VARCHAR(10) UNIQUE NOT NULL,
                    student_id VARCHAR(20) NOT NULL,
                    student_name VARCHAR(100) NOT NULL,
                    form_class VARCHAR(20) NOT NULL,
                    payment_date DATE NOT NULL,
                    deposit_slip_ref VARCHAR(50) NOT NULL,
                    fee_type VARCHAR(10) NOT NULL,
                    amount_paid FLOAT NOT NULL,
                    balance FLOAT NOT NULL,
                    installment_number INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✓ Created Receipt table")
        else:
            print("✓ Receipt table already exists")
        
        # Update existing students to have default sex if not set
        cursor.execute("UPDATE Student SET sex = 'Male' WHERE sex IS NULL OR sex = ''")
        
        # Update installment counts for existing students
        cursor.execute("""
            UPDATE Student 
            SET pta_installments = CASE 
                WHEN pta_amount_paid > 0 THEN 1 
                ELSE 0 
            END,
            sdf_installments = CASE 
                WHEN sdf_amount_paid > 0 THEN 1 
                ELSE 0 
            END
        """)
        
        # Create receipts for existing income records
        cursor.execute("SELECT COUNT(*) FROM Receipt")
        receipt_count = cursor.fetchone()[0]
        
        if receipt_count == 0:
            print("Creating receipts for existing income records...")
            cursor.execute("""
                SELECT 
                    student_id, student_name, form_class, payment_date, 
                    payment_reference, fee_type, amount_paid, balance
                FROM Income 
                ORDER BY created_at
            """)
            
            income_records = cursor.fetchall()
            receipt_number = 1
            
            for record in income_records:
                receipt_no = f"{receipt_number:04d}"
                cursor.execute("""
                    INSERT INTO Receipt (
                        receipt_no, student_id, student_name, form_class,
                        payment_date, deposit_slip_ref, fee_type, amount_paid, balance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (receipt_no, record[0], record[1], record[2], record[3], 
                      record[4], record[5], record[6], record[7]))
                receipt_number += 1
            
            print(f"✓ Created {len(income_records)} receipts")
        
        conn.commit()
        print("✓ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
