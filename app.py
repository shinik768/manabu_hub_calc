import os
import openai
import sympy as sp
import time
import re
import numpy as np
import matplotlib.pyplot as plt
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
    TextMessage,
    ImageMessage
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
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

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
    expression = re.sub(r'(?<=[^\s\+\-])(?=[\+\-])', ' ', expression)
    return expression

def add_multiplication_sign(expression):
    expression = re.sub(r'(?<=[\d])(?=[a-zA-Z])', '*', expression)  # 数字と変数の間
    expression = re.sub(r'(?<=[a-zA-Z])(?=[(])', '*', expression)  # 変数と括弧の間
    return expression

def add_exponentiation_sign(expression):
    expression = re.sub(r'(?<=[\d])\^', '**', expression)  # ^を**に変換
    return expression

def plot_graph(left_expr, right_expr, var1, var2):
    # 変数の範囲を設定
    x_vals = np.linspace(-10, 10, 400)  # xの範囲
    y_vals = np.linspace(-10, 10, 400)  # yの範囲
    X, Y = np.meshgrid(x_vals, y_vals)

    # 左辺と右辺の差を計算
    Z = sp.lambdify((var1, var2), left_expr - right_expr, 'numpy')(X, Y)  # Z = 0 になる部分を計算

    plt.figure(figsize=(8, 6))
    plt.contour(X, Y, Z, levels=[0], colors='blue')  # 等高線を描画
    plt.title(f'Graph of {sp.pretty(left_expr)} = {sp.pretty(right_expr)}')
    plt.xlabel(var1)
    plt.ylabel(var2)
    plt.grid()
    plt.axhline(0, color='black', linewidth=0.5, ls='--')
    plt.axvline(0, color='black', linewidth=0.5, ls='--')
    plt.xlim(-10, 10)
    plt.ylim(-10, 10)

    # 画像を保存
    image_path = 'graph.png'
    plt.savefig(image_path)
    plt.close()  # プロットを閉じる
    return image_path

def simplify_or_solve(expression):
    try:
        expression = add_spaces(expression)
        expression = add_multiplication_sign(expression)
        expression = add_exponentiation_sign(expression)

        equal_sign_count = expression.count('=')

        if equal_sign_count == 1:
            left_side, right_side = expression.split('=')
            left_expr = sp.sympify(left_side.strip())
            right_expr = sp.sympify(right_side.strip())

            # 変数の取得
            variables = list(left_expr.free_symbols.union(right_expr.free_symbols))
            if len(variables) == 2:
                var1, var2 = sorted(variables, key=lambda v: str(v))  # アルファベット順でソート
                image_path = plot_graph(left_expr, right_expr, str(var1), str(var2))  # グラフを描画
                return image_path  # 画像パスを返す
            elif len(variables) == 1:
                eq = sp.Eq(left_expr, right_expr)
                solution = sp.solve(eq, variables[0])
                return f"{variables[0]} = {solution[0]}" if solution else "解なし"

            return "方程式には2つの変数を含めてください！"

        elif equal_sign_count > 1:
            return "方程式には等号 (=) をちょうど1個含めてください！"
        else:
            simplified_expr = sp.simplify(sp.sympify(expression))
            simplified_expr_str = str(simplified_expr).replace('*', '')
            return f"{simplified_expr_str}"

    except (sp.SympifyError, TypeError) as e:
        print(f"SymPy error: {e}")
        return "数式または方程式を正しく入力してください！"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    try:
        ai_response = simplify_or_solve(user_message)
        if ai_response.endswith('.png'):
            # 画像パスが返された場合は画像を送信
            image_url = os.path.abspath(ai_response)  # 画像の絶対パスを取得
            with open(image_url, 'rb') as image_file:
                line_bot_api = MessagingApi(ApiClient(configuration))
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[ImageMessage(original_content_url=image_url, preview_image_url=image_url)]
                    )
                )
        else:
            # テキスト応答の場合
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=ai_response)]
                    )
                )
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
