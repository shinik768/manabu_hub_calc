import os
import openai

from os.path import join, dirname

from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

#from dotenv import load_dotenv

app = Flask(__name__)

"""
load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
"""

configuration = Configuration(access_token='555PuOD9CCSli2bcvs2PtWKO1TPixYgqg7ZmqRgVoqUTPko+RmQG65KaCAZNKGcO0xGd8fj3LGbkQvteTwr3EV+x4kuba/boP+YTFrS3KQvf/1di47nhtxeheXf7Pf6rYqU3OONhiwZKdN7FEUftYQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('4262a7e6930a464d7af5f2c76e9ad7c0')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

openai.api_key = "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"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # 使用するモデル
            prompt=user_message,
            max_tokens=1024,  # 生成するトークンの最大数
            n=1,
            stop=None,
            temperature=0.5,
        )
        ai_response = response.choices[0].text.strip()

    except openai.error.APIError as e:
        print(f"OpenAI API Error: {e}")
        ai_response = "現在、システムが混み合っているため、しばらくお待ちください。"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_response)]
            )
        )

if __name__ == "__main__":
    app.run()