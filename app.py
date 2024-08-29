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

def add_multiplication_sign(expression):
    # 数字と変数の間に乗算記号 (*) を追加
    expression = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expression)
    return expression

def simplify_or_solve(expression):
    try:
        # 入力された式のフォーマットを調整
        expression = add_spaces(expression)
        expression = add_multiplication_sign(expression)

        # デバッグ出力: 調整後の式
        print(f"Processed expression: {expression}")

        # 入力された式をSymPyでシンボリックに変換
        expr = sp.sympify(expression)

        # デバッグ出力: sympify後の式
        print(f"SymPy expression: {expr}")

        if isinstance(expr, sp.Equality):
            variables = expr.free_symbols

            if len(variables) > 0:
                solutions = {}
                for var in variables:
                    solution = sp.solve(expr, var)
                    solutions[var] = solution
                # 解を指定された形式で整形
                result = "\n".join([f"{var} = {sol}" for var, sol in solutions.items()])
                return result
            else:
                return "エラー: 方程式に変数が含まれていません。"
        else:
            simplified_expr = sp.simplify(expr)
            # '*' を省略した形式で出力
            simplified_expr_str = str(simplified_expr).replace('*', '')
            return f"簡略化された式: {simplified_expr_str}"
    except (sp.SympifyError, TypeError) as e:
        print(f"SymPy error: {e}")  # エラー内容を出力
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