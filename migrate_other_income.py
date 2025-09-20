#!/usr/bin/env python3
"""
Migrate OtherIncome table to new structure
"""

from app import app, db
import sqlite3

def migrate_other_income():
    with app.app_context():
        # Connect directly to SQLite to modify table structure
        conn = sqlite3.connect('instance/smartfee.db')
        cursor = conn.cursor()
        
        try:
            # Check if the table exists and get its structure
            cursor.execute("PRAGMA table_info(other_income)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'income_type' not in columns:
                print("Migrating other_income table...")
                
                # Create new table with correct structure
                cursor.execute('''
                    CREATE TABLE other_income_new (
                        id INTEGER PRIMARY KEY,
                        date DATE NOT NULL,
                        customer_name VARCHAR(100) NOT NULL,
                        income_type VARCHAR(50) NOT NULL,
                        total_charge FLOAT NOT NULL,
                        amount_paid FLOAT NOT NULL,
                        balance FLOAT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Copy existing data if any (map old columns to new)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='other_income'")
                if cursor.fetchone():
                    try:
                        cursor.execute('''
                            INSERT INTO other_income_new (id, date, customer_name, income_type, total_charge, amount_paid, balance, created_at)
                            SELECT id, date, customer_name, 
                                   COALESCE(rental_type, 'Other') as income_type,
                                   COALESCE(rate, amount_paid) as total_charge,
                                   amount_paid, balance, created_at
                            FROM other_income
                        ''')
                        print(f"Migrated {cursor.rowcount} existing records")
                    except sqlite3.Error as e:
                        print(f"No existing data to migrate: {e}")
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE IF EXISTS other_income")
                cursor.execute("ALTER TABLE other_income_new RENAME TO other_income")
                
                conn.commit()
                print("Migration completed successfully!")
            else:
                print("Table already has correct structure")
                
        except sqlite3.Error as e:
            print(f"Migration error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == '__main__':
    migrate_other_income()