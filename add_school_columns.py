from app import app, db
import sqlite3

def add_missing_columns():
    with app.app_context():
        try:
            # Use raw SQL to add columns
            db.engine.execute("ALTER TABLE school_configuration ADD COLUMN school_address TEXT")
            print("Added school_address column")
        except Exception as e:
            if "duplicate column" not in str(e):
                print(f"Error adding school_address: {e}")
        
        try:
            db.engine.execute("ALTER TABLE school_configuration ADD COLUMN head_teacher_contact TEXT")
            print("Added head_teacher_contact column")
        except Exception as e:
            if "duplicate column" not in str(e):
                print(f"Error adding head_teacher_contact: {e}")
        
        try:
            db.engine.execute("ALTER TABLE school_configuration ADD COLUMN bursar_contact TEXT")
            print("Added bursar_contact column")
        except Exception as e:
            if "duplicate column" not in str(e):
                print(f"Error adding bursar_contact: {e}")
        
        try:
            db.engine.execute("ALTER TABLE school_configuration ADD COLUMN school_email TEXT")
            print("Added school_email column")
        except Exception as e:
            if "duplicate column" not in str(e):
                print(f"Error adding school_email: {e}")
        
        print("Schema update completed!")

if __name__ == "__main__":
    add_missing_columns()
