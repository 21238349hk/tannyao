import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'study_user',
    'password': 'password',
    'database': 'study_chatbot'
}

def get_db_connection():
    print("Attempting to connect to the database...")  # 確認用
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Connection established successfully!")
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection failed: {e}")  # ここでエラーメッセージを取得
        return None

if __name__ == "__main__":
    print("Starting program...")
    conn = get_db_connection()

    if conn is None:
        print("Failed to connect to the database.")
    else:
        conn.close()
