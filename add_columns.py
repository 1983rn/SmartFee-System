import sqlite3

def add_columns():
    conn = sqlite3.connect('smartfee.db')
    cursor = conn.cursor()
    
    columns = [
        'school_address TEXT',
        'head_teacher_contact TEXT', 
        'bursar_contact TEXT',
        'school_email TEXT'
    ]
    
    for column in columns:
        try:
            cursor.execute(f'ALTER TABLE school_configuration ADD COLUMN {column}')
            print(f'Added {column}')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e):
                print(f'{column} already exists')
            else:
                print(f'Error adding {column}: {e}')
    
    conn.commit()
    conn.close()
    print('Done')

if __name__ == '__main__':
    add_columns()
