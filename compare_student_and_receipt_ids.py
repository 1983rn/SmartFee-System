# compare_student_and_receipt_ids.py
"""
This script lists all unique student_id values in both the student and receipt tables, and shows mismatches.
"""
import sqlite3
from tabulate import tabulate

DB_PATH = 'instance/smartfee.db'

def get_unique_ids(table, column):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT DISTINCT {column} FROM {table}")
        return set(row[0] for row in cur.fetchall())

def main():
    student_ids = get_unique_ids('student', 'student_id')
    receipt_ids = get_unique_ids('receipt', 'student_id')

    print("Total unique student.student_id:", len(student_ids))
    print("Total unique receipt.student_id:", len(receipt_ids))

    only_in_students = student_ids - receipt_ids
    only_in_receipts = receipt_ids - student_ids

    print("\nStudent IDs only in student table (no receipts):")
    print(tabulate([[sid] for sid in sorted(only_in_students)], headers=["student_id"]))

    print("\nStudent IDs only in receipt table (no matching student):")
    print(tabulate([[sid] for sid in sorted(only_in_receipts)], headers=["student_id"]))

    print("\nSample of matching IDs:")
    print(tabulate([[sid] for sid in sorted(student_ids & receipt_ids)][:10], headers=["student_id"]))

if __name__ == "__main__":
    main()
