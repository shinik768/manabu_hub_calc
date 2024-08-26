import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

app = Flask(__name__)

port = int(os.environ.get("PORT", 5000))

# ロギングの設定
logging.basicConfig(level=logging.ERROR)

# 環境変数からLINE APIの設定を取得
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

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
