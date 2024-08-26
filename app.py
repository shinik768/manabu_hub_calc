from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import logging

app = Flask(__name__)

port = int(os.environ.get("PORT", 5000))

# ロギングの設定
logging.basicConfig(level=logging.ERROR)

line_bot_api = LineBotApi(
    'd580vu4FvFiDqyU6Qxi3xhbx8d24lOFcGDKREcASB3QQdIjhq2+wq22Dcml1RMHf0xGd8fj3LGbkQvteTwr3EV+x4kuba/boP+YTFrS3KQt5hIzSY96Tqu0khsEbCKgelGZDv/KRlDmjeEVHEoqYHQdB04t89/1O/w1cDnyilFU='
)
handler = WebhookHandler('ede248563361ab924f8f81e7c425038b')

@app.route('/')
def home():
    return "<p>Hello, World!</p>"

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
    # LINEに応答を送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Hello, World!")  # ここで応答を設定
    )

@app.errorhandler(Exception)
def handle_exception(e):
    # エラーメッセージをログに記録
    logging.error(f"An error occurred: {str(e)}")
    return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)





