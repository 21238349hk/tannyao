from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

 ## ここはSQLの設定。まだ書いてない
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    # 'password': '',
    # 'database': '',
    'port': 3306,
}


# ここもまだ途中。これから中身を作成していく
@app.route("/")
def index():
    return render_template("index.html")

# ログイン処理の中身
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # データベースからユーザー名とユーザーパスワードを取得
            username = request.form['username']
            password = request.form['password']

            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # ここも途中。作成したデータベースによってSQL構文が変わるため。下のuserはこのSQL構文から取得したユーザーデータを取得する処理
            cursor.execute("SELECT * from .....")
            user = cursor.fetchone()

            # ここら辺は閉じる
            cursor.close()
            connection.close()
        
        except Exception as e:
            print(f"error occured: {e}")
            return f"error detail: {e}"

    return render_template('result_login.html')



    return render_template("login.html")


# チャットボッと入力後の遷移画面
@app.route("/answer")
def login():
    return render_template("answer.html")

if __name__ == "__main__":
    app.run(debug=True)