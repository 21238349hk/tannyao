from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
import os
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime
from db import get_db_connection  
app = Flask(__name__)
app.secret_key = os.urandom(24)  

@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        flash("⚠ ログインしてください！", "error")
        return redirect(url_for("login"))

    username = session.get("username")

    return render_template("index.html", username=username)

@app.route("/register", methods=['GET', 'POST'])
def register():
    message = None  
    message_type = None  

    if request.method == "POST":
        try:
            username = request.form['username']
            password = request.form['password']
            hashed_password = generate_password_hash(password)

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                message = "⚠ このユーザー名は既に登録されています。別の名前をお試しください。"
                message_type = "error"
            else:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed_password)
                )
                connection.commit()

                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user:
                    session['user_id'] = user[0]
                    session['username'] = username
                    message = f" 登録成功！ようこそ、{username} さん！"
                    message_type = "success"
                    return redirect(url_for('index'))

            cursor.close()
            connection.close()

        except Exception as e:
            message = f"⚠ 登録中にエラーが発生しました: {e}"
            message_type = "error"

    return render_template('register.html', message=message, message_type=message_type)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            cursor.close()
            connection.close()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash("✅ ログイン成功！", "success")
                return redirect(url_for("index"))  
            else:
                flash("⚠ ユーザー名またはパスワードが間違っています！", "error")

        except Exception as e:
            flash(f"エラーが発生しました: {e}", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("👋 ログアウトしました！", "info")
    return redirect(url_for("login"))

@app.route("/study_history", methods=["GET", "POST"])
def study_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        try:
            data = request.get_json()
            study_date = data["date"]  # "2025-03-01" のような形式
            subject = data["subject"]
            hours = float(data["hours"])

            connection = get_db_connection()
            cursor = connection.cursor()

            # データベースに勉強記録を追加
            cursor.execute(
                "INSERT INTO study_records (user_id, date, subject, hours) VALUES (%s, %s, %s, %s)",
                (user_id, study_date, subject, hours)
            )
            connection.commit()

            cursor.close()
            connection.close()

            return jsonify({"success": True, "message": "勉強記録が追加されました！"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT date, subject, hours FROM study_records WHERE user_id = %s ORDER BY date DESC",
        (user_id,)
    )
    study_records = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("study_history.html", study_records=study_records)

@app.route('/statistics')
def statistics():
    if "user_id" not in session:
        flash("ログインしてください", "error")
        return redirect(url_for("login"))

    return render_template('statistics.html')

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        flash("ログインしてください", "error")
        return redirect(url_for("login"))

    return render_template('settings.html')

@app.route("/goals", methods=["GET", "POST"])
def goals():
    if request.method == "POST":
        goal = request.form.get("goal")
        target_date = request.form.get("target_date")

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO study_goals (user_id, goal, target_date, progress) VALUES (1, %s, %s, 0)", (goal, target_date))
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("goals"))

    connection = get_db_connection()
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