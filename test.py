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
            response = model.generate_content(text)

            print("Geminiの応答:")
            print(response.text)

        except sr.UnknownValueError:
            print("音声を認識できませんでした。")
        except sr.RequestError as e:
            print(f"音声認識サービスへのリクエストに失敗しました: {e}")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    speech_to_text_to_gemini()