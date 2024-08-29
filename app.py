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

def add_exponentiation_sign(expression):
    # `^` を `**` に変換
    expression = expression.replace('^', '**')
    return expression

def process_derivatives(expression):
    # 微分を表すための処理
    # 文字の直後にある'を削除して、微分の階数を示す
    derivative_count = {char: expression.count(char + "'") for char in set(expression) - set("0123456789+-*/()= ")}
    for char, count in derivative_count.items():
        if count > 0:
            # 'を置換し、微分の階数に応じて微分を適用
            for _ in range(count):
                expression = expression.replace(char + "'", f"sp.diff({char})")
    return expression, any(derivative_count.values())

def simplify_or_solve(expression):
    try:
        # 入力された式のフォーマットを調整
        expression = add_spaces(expression)
        expression = add_multiplication_sign(expression)
        expression = add_exponentiation_sign(expression)

        # 微分の処理
        expression, is_differential_equation = process_derivatives(expression)

        # `=` の数をカウント
        equal_sign_count = expression.count('=')

        if is_differential_equation:
            # 微分方程式の処理
            solution = solve_differential_equation(expression)
            return solution
        elif equal_sign_count == 1:
            # 左辺と右辺に分割
            left_side, right_side = expression.split('=')
            left_expr = sp.sympify(left_side)
            right_expr = sp.sympify(right_side)

            # 方程式を解く
            variables = left_expr.free_symbols
            if len(variables) > 0:
                solutions = {}
                for var in variables:
                    solution = sp.solve(left_expr - right_expr, var)
                    # 解が存在するか確認
                    if solution:
                        solutions[var] = solution[0] if len(solution) == 1 else solution
                    else:
                        solutions[var] = "解なし"  # 解がない場合の処理
                # 解を指定された形式で整形
                result = "\n".join([f"{var} = {sol}" for var, sol in solutions.items()])
                return result
            else:
                return "方程式には変数を含めてください！"
        elif equal_sign_count > 1:
            return "方程式には等号 (=) をちょうど1個含めてください！"
        else:
            # それ以外は式の簡略化
            simplified_expr = sp.simplify(sp.sympify(expression))
            simplified_expr_str = str(simplified_expr).replace('*', '')
            return f"簡略化された式: {simplified_expr_str}"
    except (sp.SympifyError, TypeError) as e:
        print(f"SymPy error: {e}")  # エラー内容を出力
        return "数式または方程式を正しく入力してください！"

def solve_differential_equation(equation):
    # 微分方程式を解く機能を追加
    try:
        # 微分方程式の処理
        solution = sp.dsolve(sp.sympify(equation))
        return f"微分方程式の解: {solution}" if solution else "解なし"
    except Exception as e:
        print(f"解けない微分方程式: {e}")  # 解けない場合はコメントを出力
        return "エラー: 微分方程式の解決中にエラーが発生しました。"

    
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