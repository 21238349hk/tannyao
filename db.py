import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'study_user',
    'password': 'password',
    'database': 'study_chatbot',
    'use_pure': True  # ← 追加
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

if __name__ == "__main__":
    conn = get_db_connection()
    if conn.is_connected():
        print("Success study_chatbot's database")
    conn.close()