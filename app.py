from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
import os
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime
from db import get_db_connection  
import google.generativeai as genai
import speech_recognition as sr  # 音声認識

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

    #新しく音声認識の要約データを取得

    cursor.execute(
        "SELECT id, subject, title, summary, created_at FROM study_notes WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    study_notes = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "study_history.html",
        study_records=study_records,
        study_notes = study_notes #新しく追加
    )

@app.route("/statistics")
def statistics():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT date, subject, hours FROM study_records
        WHERE user_id = %s
        ORDER BY date ASC
    """, (user_id,))
    records = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("statistics.html", study_records=records)




#新たに追加した部分
# Google Gemini API の設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")

@app.route("/api/process_audio", methods=["POST"])
def process_audio():
    """フロントエンドから送られた音声テキストを処理し、データベースに保存"""
    if "user_id" not in session:
        return jsonify({"error": "ログインしてください"}), 401

    data = request.get_json()
    user_text = data.get("text", "")

    if not user_text:
        return jsonify({"error": "テキストがありません"}), 400

    # Gemini API で処理
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = (
        "あなたは教育用AIアシスタントです。\n"
        "ユーザーは今日勉強したことを話します。\n\n"
        "1. ユーザーの発言から適切な「科目」を特定してください。なお，「英語」,「国語」.「数学」,「プログラミング」,「理科」,「社会」のいづれかに分類すること．\n"
        "2. 仮に，ユーザが発言した内容に誤りがある場合は適切に修正し,ユーザに知らせてください\n"
        "3. ユーザーの発言に基づき、以下のフォーマットで整理してください。なお，内容を修正した場合は修正内容をフォーマットにいれること\n\n"
        "4. ユーザが勉強したことではなく，日常会話をした場合はそのまま会話をしてください"
        "※要約部分では余計な情報を追加せず、ユーザーの話した内容を簡潔にまとめてください。\n\n"
        "【出力フォーマット】\n"
        "科目: [適切な科目]\n"
        "タイトル: [適切なタイトル]\n"
        "要約: [簡単な要約]\n\n"
        f"ユーザーの入力:\n{user_text}"
    )

    response = model.generate_content(prompt)
    response_text = response.text
    print(response_text)

    chat_part = response_text.split("【出力フォーマット】")[0].strip()

    # 科目、タイトル、要約を抽出
    subject, title, summary = "", "", ""
    for line in response_text.split("\n"):
        if line.startswith("科目:"):
            subject = line.replace("科目:", "").strip()
        elif line.startswith("タイトル:"):
            title = line.replace("タイトル:", "").strip()
        elif line.startswith("要約:"):
            summary = line.replace("要約:", "").strip()

    print(repr(subject))


    # データベースに保存
    if subject.strip() in ["英語", "国語", "数学", "プログラミング", "理科", "社会"]:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO study_notes (user_id, subject, title, summary, created_at) VALUES (%s, %s, %s, %s, NOW())",
                (session["user_id"], subject, title, summary)
            )
            connection.commit()

            cursor.close()
            connection.close()
        except Exception as e:
            return jsonify({"error": f"データベース保存エラー: {e}"}), 500

    return jsonify({
        "subject": subject,
        "title": title,
        "summary": summary,
        "full_response": chat_part
    })

@app.route("/delete_study_note", methods=["POST"]) ## データベースからstudy_noteのデータを削除するエンドポイント
def delete_study_note():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "ログインしてください"}), 401

    data = request.get_json()
    note_id = data.get("note_id")

    if not note_id:
        return jsonify({"success": False, "error": "削除するデータが指定されていません"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # ユーザーのデータのみ削除できるようにする
        cursor.execute(
            "DELETE FROM study_notes WHERE id = %s AND user_id = %s",
            (note_id, session["user_id"])
        )
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({"success": True, "message": "データが削除されました！"})
    except Exception as e:
        return jsonify({"success": False, "error": f"削除エラー: {e}"}), 500

@app.route("/goals", methods=["GET", "POST"])#未来の目標
def goals():
    if "user_id" not in session:
        flash("ログインしてください", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        title = request.form.get("title")
        deadline = request.form.get("deadline")
        category = request.form.get("category")
        progress = request.form.get("progress", 0)
        memo = request.form.get("memo", "")


        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO study_goals (user_id, goal, target_date, category, progress, memo, done)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
        """, (user_id, title, deadline, category, progress, memo))
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("goals"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT goal AS title, target_date AS deadline, category, progress, memo, done, id FROM study_goals WHERE user_id = %s", (user_id,))
    goals = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("goals.html", goals=goals)

@app.route("/update_goal/<int:id>", methods=["POST"])
def update_goal(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    done = 'done' in request.form  # チェックボックスのON/OFF

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE study_goals SET done = %s WHERE id = %s AND user_id = %s",
        (done, id, user_id)
    )
    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for("goals"))

@app.route("/delete_goal/<int:id>", methods=["POST"])
def delete_goal(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM study_goals WHERE id = %s AND user_id = %s",
        (id, user_id)
    )
    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for("goals"))

@app.route("/settings", methods=["GET", "POST"])#設定
def settings():
    if "user_id" not in session:
        flash("ログインしてください", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        study_goal = request.form.get("study_goal", type=int)
        notifications = request.form.get("notifications")
        theme = request.form.get("theme")
        font_size = request.form.get("font_size")
        language = request.form.get("language")

        cursor.execute("SELECT user_id FROM user_settings WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE user_settings
                SET study_goal=%s, notifications=%s, theme=%s, font_size=%s, language=%s
                WHERE user_id=%s
            """, (study_goal, notifications, theme, font_size, language, user_id))
        else:
            cursor.execute("""
                INSERT INTO user_settings (user_id, study_goal, notifications, theme, font_size, language)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, study_goal, notifications, theme, font_size, language))

        connection.commit()
        flash("✅ 設定を保存しました", "success")
        return redirect(url_for("settings"))

    # GET：現在の設定を読み込み
    cursor.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
    settings = cursor.fetchone() or {}

    cursor.close()
    connection.close()

    return render_template("settings.html", **settings)


# チャットボッと入力後の遷移画面
### @app.route("/answer")
### def login():
    # return render_template("answer.html")

if __name__ == "__main__":
    app.run(debug=True)