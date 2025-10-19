import sqlite3

conn = sqlite3.connect('smartfee.db')
cursor = conn.cursor()

cursor.execute("SELECT id, activity_service, is_category FROM budget ORDER BY id LIMIT 30;")
results = cursor.fetchall()

print("Current budget order:")
for row in results:
    category_marker = "[CATEGORY]" if row[2] else "[ACTIVITY]"
    print(f"{row[0]:2d}: {category_marker} {row[1]}")

conn.close()