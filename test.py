import speech_recognition as sr
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def speech_to_text_to_gemini():
    """音声認識でテキスト化し、Gemini APIに渡す関数"""

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("何か話してください...")
        audio = recognizer.listen(source)

        try:
            print("音声を認識中...")
            text = recognizer.recognize_google(audio, language="ja-JP")
            print(f"認識されたテキスト: {text}")

            # Gemini-2.0-flashにテキストを渡して応答を得る
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = (
                "あなたは教育用AIアシスタントです。\n"
                "ユーザーは勉強したことを話します。もし間違った知識がある場合は訂正をし、"
                "ユーザーが話したことについて、以下のフォーマットで応答してください。なお，要約部分では，余計なことは追加せず，ユーザが話した内容に基づいて要約してください\n\n"
                "タイトル: [適切なタイトル]\n"
                "要約: [簡単な要約]\n\n"
                "ユーザーの入力:\n" + text
            )

            response = model.generate_content(prompt)
            response_text = response.text
            print(response.text)

            # タイトルと要約を抽出
            title = ""
            summary = ""
            for line in response_text.split("\n"):
                if line.startswith("タイトル:"):
                    title = line.replace("タイトル:", "").strip()
                elif line.startswith("要約:"):
                    summary = line.replace("要約:", "").strip()

            print("\n🔹 タイトル:", title)
            print("📝 要約:", summary)

        except sr.UnknownValueError:
            print("音声を認識できませんでした。")
        except sr.RequestError as e:
            print(f"音声認識サービスへのリクエストに失敗しました: {e}")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    speech_to_text_to_gemini()
