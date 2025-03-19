import mysql.connector
import hashlib
from db import get_db_connection


## 確認用のコード

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', 
                       (username, hash_password(password)))
        conn.commit()
        print(f"ユーザー {username} を登録しました")
    except mysql.connector.IntegrityError:
        print("ユーザー名が既に存在します")
    
    conn.close()

def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, password FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()

    conn.close()

    if user and user[1] == hash_password(password):
        print(f" {username}' login success")
        return user[0]  
    else:
        print("mistake password")
        return None

if __name__ == "__main__":
    register_user("test_user", "test_password")
    login_user("test_user", "test_password")
