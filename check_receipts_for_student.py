# check_receipts_for_student.py
"""
This script checks for receipts for a specific student_id and prints them out.
"""
import sqlite3
from tabulate import tabulate

DB_PATH = 'instance/smartfee.db'

def get_receipts_for_student(student_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM receipt WHERE student_id = ?", (student_id,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        return columns, rows

def main():
    student_id = input("Enter the student_id to check receipts for: ").strip()
    columns, rows = get_receipts_for_student(student_id)
    if not rows:
        print(f"No receipts found for student_id: {student_id}")
    else:
        print(f"Receipts for student_id: {student_id}")
        print(tabulate(rows, headers=columns))

if __name__ == "__main__":
    main()
