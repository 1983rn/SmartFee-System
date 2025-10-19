import sqlite3
import base64

def is_base64(s):
    try:
        return base64.urlsafe_b64encode(base64.urlsafe_b64decode(s)) == s.encode()
    except Exception:
        return False

def main():
    DB_PATH = 'instance/smartfee.db'
    TABLE = 'student'
    FIELDS = ['student_id', 'name', 'sex', 'form_class', 'parent_phone']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'SELECT id, {', '.join(FIELDS)} FROM {TABLE}')
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        student_id = row[0]
        updates = {}
        for idx, field in enumerate(FIELDS, start=1):
            value = row[idx]
            if value and is_base64(value):
                updates[field] = None
        if updates:
            set_clause = ', '.join([f"{k} = NULL" for k in updates.keys()])
            cursor.execute(f"UPDATE {TABLE} SET {set_clause} WHERE id = ?", (student_id,))
            updated += 1
    conn.commit()
    print(f'Updated {updated} student records with cleaned fields.')
    conn.close()

if __name__ == '__main__':
    main()
