import sqlite3

DB_PATH = 'instance/smartfee.db'
TABLE = 'student'
FIELDS = ['student_id', 'name', 'sex', 'form_class', 'parent_phone']

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'SELECT id FROM {TABLE}')
    rows = cursor.fetchall()
    for row in rows:
        student_id = row[0]
        print(f"For Student ID {student_id}, please enter the correct values (leave blank to skip):")
        updates = {}
        for field in FIELDS:
            value = input(f"  {field}: ")
            if value.strip():
                updates[field] = value.strip()
        if updates:
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            params = list(updates.values()) + [student_id]
            cursor.execute(f"UPDATE {TABLE} SET {set_clause} WHERE id = ?", params)
            print(f"  Updated fields: {', '.join(updates.keys())}")
        else:
            print("  No changes made.")
    conn.commit()
    conn.close()
    print('Done!')

if __name__ == '__main__':
    main()
