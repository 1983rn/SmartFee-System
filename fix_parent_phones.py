import sqlite3
import base64
from cryptography.fernet import Fernet, InvalidToken

DB_PATH = 'instance/smartfee.db'

# If you know the encryption key used for phone numbers, set it here
# Otherwise, this script will just blank out encrypted values
ENCRYPTION_KEY = None  # Example: b'your-fernet-key-here'

def is_base64(s):
    try:
        return base64.urlsafe_b64encode(base64.urlsafe_b64decode(s)) == s.encode()
    except Exception:
        return False

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT id, parent_phone FROM student')
    rows = cursor.fetchall()

    updated = 0
    for row in rows:
        student_id, phone = row
        if phone and is_base64(phone):
            if ENCRYPTION_KEY:
                try:
                    f = Fernet(ENCRYPTION_KEY)
                    decrypted = f.decrypt(base64.urlsafe_b64decode(phone)).decode()
                    # Remove any padding if present (e.g., phone_XXXXXXXX)
                    if '_' in decrypted:
                        decrypted = decrypted.split('_')[0]
                    cursor.execute('UPDATE student SET parent_phone = ? WHERE id = ?', (decrypted, student_id))
                    updated += 1
                except InvalidToken:
                    print(f'Could not decrypt phone for student id {student_id}, blanking it.')
                    cursor.execute('UPDATE student SET parent_phone = NULL WHERE id = ?', (student_id,))
                    updated += 1
            else:
                # No key, just blank out
                cursor.execute('UPDATE student SET parent_phone = NULL WHERE id = ?', (student_id,))
                updated += 1
    conn.commit()
    print(f'Updated {updated} phone numbers.')
    conn.close()

if __name__ == '__main__':
    main()
