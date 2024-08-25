from llama_index import GPTIndex
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

port = int(os.environ.get("PORT", 5000))

@app.route('/')
def home():
    return 'Hello, World!'

line_bot_api = LineBotApi(
    'd580vu4FvFiDqyU6Qxi3xhbx8d24lOFcGDKREcASB3QQdIjhq2 \
    +wq22Dcml1RMHf0xGd8fj3LGbkQvteTwr3EV+x4kuba/boP+YTF \
    rS3KQt5hIzSY96Tqu0khsEbCKgelGZDv/KRlDmjeEVHEoqYHQdB \
    04t89/1O/w1cDnyilFU='
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
    openai.api_key = 'sk-proj-hm82lsi0epYJW5UJ0E7G9iM9T \
        c2-9zsLy64E6tv1foLV1ryeX1hiAxW5r_T3BlbkFJc2jB6x \
        03cJ3GK5YzRcqe1u-c5W3ArJH3TRVNMFdt1h7QFdNE3C1CINxecA'
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
    return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)

