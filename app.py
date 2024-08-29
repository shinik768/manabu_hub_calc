import os
import openai
import sympy as sp
import time
import re

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

app = Flask(__name__)

configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))


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

openai.api_key = os.environ.get('OPENAI_API_KEY')

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

def add_spaces(expression):
    # `+` と `-` の前にスペースを追加
    expression = re.sub(r'(?<=[^\s\+\-])(?=[\+\-])', ' ', expression)
    return expression

def simplify_or_solve(expression):
    try:
        # 入力された式のフォーマットを調整
        expression = add_spaces(expression)
        
        # 入力された式をSymPyでシンボリックに変換
        expr = sp.sympify(expression)

        # 式が等式 (方程式) である場合
        if isinstance(expr, sp.Equality):
            # 方程式の変数を取得
            variables = expr.free_symbols

            if len(variables) > 0:
                # 複数の変数に対して解を求める
                solutions = {}
                for var in variables:
                    solution = sp.solve(expr, var)
                    solutions[var] = solution
                return {str(var): sol for var, sol in solutions.items()}
            else:
                return "エラー: 方程式に変数が含まれていません。"
        else:
            # それ以外は式の簡略化
            simplified_expr = sp.simplify(expr)
            return f"簡略化された式: {simplified_expr}"
    except (sp.SympifyError, TypeError):
        return "エラー: 数式または方程式を正しく入力してください。"
    
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    try:
        #response = send_request_with_retry(user_message)
        #ai_response = response.choices[0].message.content.strip()
        ai_response = simplify_or_solve(user_message)
    except Exception as e:
        print(f"Error: {e}")
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
    port = int(os.environ.get("PORT"))
    app.run(host='0.0.0.0', port=port)