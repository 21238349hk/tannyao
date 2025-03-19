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
                "ユーザーは今日勉強したことを話します。\n\n"
                "1. ユーザーの発言から適切な「科目」を特定してください。\n"
                "2. 仮に，ユーザが発言した内容に誤りがある場合は適切に修正し、正しい情報を提供してください。\n"
                "3. ユーザーの発言に基づき、以下のフォーマットで整理してください。\n"
                "   ※要約部分では余計な情報を追加せず、ユーザーの話した内容を簡潔にまとめてください。\n\n"
                "【出力フォーマット】\n"
                "科目: [適切な科目]\n"
                "タイトル: [適切なタイトル]\n"
                "要約: [簡単な要約]\n\n"
                f"ユーザーの入力:\n{text}"
            )


            response = model.generate_content(prompt)
            response_text = response.text

            # 科目，タイトル，要約を抽出
            subject= ""
            title = ""
            summary = ""
            for line in response_text.split("\n"):
                if line.startswith("科目:"):
                    subject = line.replace("科目:", "").strip()
                elif line.startswith("タイトル"):
                    title = line.replace("タイトル","").strip()
                elif line.startswith("要約:"):
                    summary = line.replace("要約:", "").strip()
            
            print("\n 科目:", subject)
            print("タイトル:", title)
            print("要約:", summary)

        except sr.UnknownValueError:
            print("音声を認識できませんでした。")
        except sr.RequestError as e:
            print(f"音声認識サービスへのリクエストに失敗しました: {e}")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    speech_to_text_to_gemini()
