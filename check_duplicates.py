import sqlite3

def check_duplicate_student_ids(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = """
        SELECT student_id, COUNT(*) as count
        FROM Student
        GROUP BY student_id
        HAVING count > 1;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    if results:
        print("Duplicate student IDs found:")
        for row in results:
            print(f"Student ID: {row[0]}, Count: {row[1]}")
    else:
        print("No duplicate student IDs found.")

if __name__ == "__main__":
    db_path = "instance/smartfee.db"
    check_duplicate_student_ids(db_path)
