import sqlite3
import base64

def is_base64(s):
    try:
        return base64.urlsafe_b64encode(base64.urlsafe_b64decode(s)) == s.encode()
    except Exception:
        return False

def main():
    DB_PATH = 'instance/smartfee.db'
    TABLE = 'receipt'
    FIELD = 'student_id'
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'SELECT id, {FIELD} FROM {TABLE}')
    rows = cursor.fetchall()
    for row in rows:
        rid, student_id = row
        if student_id and is_base64(student_id):
            print(f"Receipt ID {rid} has encrypted student_id: {student_id}")
    conn.close()

if __name__ == '__main__':
    main()
