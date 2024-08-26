from llama_index import GPTIndex  # または適切なモジュール名
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import logging

from langchain import Document  # 修正

# PDFやテキストデータのインデックス化
documents = [Document.from_file("data/purpose_of_questions_japanese.pdf")]
index = GPTIndex.from_documents(documents)

# インデックスを保存して再利用
index.save_to_disk("index.json")

app = Flask(__name__)

port = int(os.environ.get("PORT", 5000))

# ロギングの設定
logging.basicConfig(level=logging.ERROR)

@app.route('/')
def home():
    return "<p>Hello, World!</p>"

line_bot_api = LineBotApi(
    'd580vu4FvFiDqyU6Qxi3xhbx8d24lOFcGDKREcASB3QQdIjhq2+wq22Dcml1RMHf0xGd8fj3LGbkQvteTwr3EV+x4kuba/boP+YTFrS3KQt5hIzSY96Tqu0khsEbCKgelGZDv/KRlDmjeEVHEoqYHQdB04t89/1O/w1cDnyilFU='
)
handler = WebhookHandler('ede248563361ab924f8f81e7c425038b')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # インデックスを読み込んでクエリ処理
    index = GPTIndex.load_from_disk("index.json")
    response = index.query(user_message)

    # ChatGPT APIを使って応答を生成
    openai.api_key = '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'
    completion = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Q: {user_message}\nA: {response}",
        max_tokens=150
    )
    bot_reply = completion.choices[0].text.strip()

    # LINEに応答を送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=bot_reply)
    )

@app.errorhandler(Exception)
def handle_exception(e):
    # エラーメッセージをログに記録
    logging.error(f"An error occurred: {str(e)}")
    return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)