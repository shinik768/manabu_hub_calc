import os
import openai
import sympy as sp
import time
import re
import numpy as np
import matplotlib.pyplot as plt
import uuid  # 追加
import threading
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
    expression = re.sub(r'(?<=[\d])(?=[(])', '*', expression)  # 数字と括弧の間
    return expression

def add_exponentiation_sign(expression):
    expression = re.sub(r'(?<=[\d])\^', '**', expression)  # ^を**に変換
    expression = re.sub(r'(?<=[a-zA-Z])(?=\d)', '**', expression)  # 文字の後に数字が来る場合
    return expression

def format_equation(left_expr, right_expr, var1, var2):
    """数式を「（文字を含む式）＝（定数）」の形に整形します。"""
    simplified_expr = sp.simplify(left_expr - right_expr)  # 左辺と右辺の差を簡略化
    constant = simplified_expr.subs({var1: 0, var2: 0})  # 定数部分を計算
    formatted_expr = str(simplified_expr).replace('*', '').replace('**', '^')  # 形式を整形
    return f"{formatted_expr} = {constant}"

def plot_graph(left_expr, right_expr, var1, var2):
    # 変数の範囲を設定
    x_vals = np.linspace(-10, 10, 400)  # xの範囲
    y_vals = np.linspace(-10, 10, 400)  # yの範囲
    X, Y = np.meshgrid(x_vals, y_vals)

    # 左辺と右辺の差を計算
    Z = sp.lambdify((var1, var2), left_expr - right_expr, 'numpy')(X, Y)  # Z = 0 になる部分を計算

    plt.figure(figsize=(8, 6))
    # タイトルを整形して設定
    graph_title = format_equation(left_expr, right_expr, var1, var2)
    plt.contour(X, Y, Z, levels=[0], colors='blue')  # 等高線を描画
    plt.title(graph_title)
    plt.xlabel(var1)
    plt.ylabel(var2)
    plt.grid()
    plt.axhline(0, color='black', linewidth=0.5, ls='--')
    plt.axvline(0, color='black', linewidth=0.5, ls='--')
    plt.xlim(-10, 10)
    plt.ylim(-10, 10)

    # ランダムな文字列を生成して画像を保存
    random_string = uuid.uuid4().hex  # ランダムな文字列を生成
    image_path = os.path.join('static', f'graph_{random_string}.png')  # staticフォルダに保存
    plt.savefig(image_path)
    plt.close()

    # 画像ファイルの存在を確認
    if os.path.exists(image_path):
        print(f"画像ファイルが保存されました: {image_path}")
    else:
        print("画像ファイルの保存に失敗しました。")
    
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

            return "方程式には1つまたは2つの変数を含めてください！"

        elif equal_sign_count > 1:
            return "方程式には等号 (=) をちょうど1個含めてください！"
        else:
            simplified_expr = sp.simplify(sp.sympify(expression))
            simplified_expr_str = str(simplified_expr).replace('*', '')
            return f"{simplified_expr_str}"

    except (sp.SympifyError, TypeError) as e:
        print(f"SymPy error: {e}")
        return "数式を正しく入力してください！"

def delete_image_after_delay(image_path, delay=86400):  # デフォルトは86400秒（24時間）
    time.sleep(delay)
    if os.path.exists(image_path):
        os.remove(image_path)
        print(f"画像ファイルが削除されました: {image_path}")

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    try:
        ai_response = simplify_or_solve(user_message)
        if ai_response.endswith('.png'):
            # 画像パスが返された場合は画像を送信
            image_path = ai_response  # 画像パスを保存
            image_url = f"https://manabu-hub-ai.onrender.com/static/{os.path.basename(image_path)}"  # RenderのURLを指定
            
            line_bot_api = MessagingApi(ApiClient(configuration))
            response = line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[ImageMessage(original_content_url=image_url, preview_image_url=image_url)]
                )
            )
            print("画像送信応答:", response)

            # 画像送信後に別スレッドで削除処理を開始
            threading.Thread(target=delete_image_after_delay, args=(image_path,)).start()
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