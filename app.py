import os
import openai
import time

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

from llama_cpp import Llama

#from dotenv import load_dotenv

app = Flask(__name__)

"""
load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
"""

llm = Llama(model_path=".models/SakanaAI-EvoLLM-JP-v1-7B-q4_K_M.gguf", n_gpu_layers=-1, n_ctx=2048)

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

def send_request_with_retry(user_message):
    for attempt in range(3):  # 最大3回のリトライ
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",  # 使用するモデル
                messages=[
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1024,
            )
            return response
        except openai.RateLimitError as e:
            print(f"Rate limit exceeded. Retrying in {2**attempt} seconds.")
            time.sleep(2**attempt)
    raise Exception("Failed to send request after multiple retries.")

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    try:
        #response = send_request_with_retry(user_message)
        #ai_response = response.choices[0].message.content.strip()
        response = llm(
            f"Q: {user_message} A: ", # Prompt
            max_tokens=32, # Generate up to 32 tokens, set to None to generate up to the end of the context window
            stop=["Q:", "\n"], # Stop generating just before the model would generate a new question
            echo=True # Echo the prompt back in the output
        )
        ai_response = response["choices"][0]["text"]
    except Exception as e:
        print(f"Error: {e}")
        ai_response = "現在、システムが混み合っているため、しばらくお待ちください。"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                #messages=[TextMessage(text=ai_response)]
                messages=[TextMessage(text=ai_response)]
            )
        )

if __name__ == "__main__":
    app.run()