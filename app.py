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

    # return render_template('result_login.html')



    return render_template("login.html")

@app.route("/study_history")
def study_history():
    return render_template("study_history.html")

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        study_goal = request.form.get("study_goal")
        notifications = request.form.get("notifications")
        theme = request.form.get("theme")

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO user_settings (user_id, daily_study_goal, notifications_enabled, theme)
            VALUES (1, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            daily_study_goal = VALUES(daily_study_goal), 
            notifications_enabled = VALUES(notifications_enabled), 
            theme = VALUES(theme)
        """, (study_goal, notifications, theme))
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("settings"))

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_settings WHERE user_id = 1")
    settings = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template("settings.html", 
                           study_goal=settings["daily_study_goal"] if settings else 30, 
                           notifications=settings["notifications_enabled"] if settings else "on",
                           theme=settings["theme"] if settings else "light")

@app.route("/goals", methods=["GET", "POST"])
def goals():
    if request.method == "POST":
        goal = request.form.get("goal")
        target_date = request.form.get("target_date")

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO study_goals (user_id, goal, target_date, progress) VALUES (1, %s, %s, 0)", (goal, target_date))
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("goals"))

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM study_goals WHERE user_id = 1")
    goals = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("goals.html", goals=goals)


# チャットボッと入力後の遷移画面
### @app.route("/answer")
### def login():
    # return render_template("answer.html")

if __name__ == "__main__":
    app.run(debug=True)