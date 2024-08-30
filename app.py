import os
import sympy as sp
import time
import re
import numpy as np
import matplotlib.pyplot as plt
import uuid
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

def clean_expression(expression):
    # アルファベット、数字、特定の記号を許容
    cleaned_expression = re.sub(r'[^a-zA-Z0-9=()!$+*-/*^]', '', expression)
    return cleaned_expression

def change_I_and_i(expression):
    expression = str(expression).replace('i', '<')
    expression = str(expression).replace('I', '>')
    expression = str(expression).replace('<', 'I')
    expression = str(expression).replace('>', 'i')
    return expression

def add_spaces(expression):
    expression = re.sub(r'(?<=[^\s\+\-])(?=[\+\-])', ' ', expression)
    return expression

def add_multiplication_sign(expression):
    expression = re.sub(r'(?<=[\d])(?=[a-zA-Z])', '*', expression)  # 数字と変数の間
    expression = re.sub(r'(?<=[a-zA-Z])(?=[a-zA-Z])', '*', expression)  # 変数と変数の間
    expression = re.sub(r'(?<=[)])(?=[a-zA-Z])', '*', expression)  # 括弧と変数の間
    expression = re.sub(r'(?<=[\d])(?=[(])', '*', expression)  # 数字と括弧の間
    expression = re.sub(r'(?<=[a-zA-Z])(?=[(])', '*', expression)  # 変数と括弧の間
    expression = re.sub(r'(?<=[)])(?=[(])', '*', expression)  # 括弧と括弧の間
    return expression

def add_exponentiation_sign(expression):
    expression = str(expression).replace('^', '**') # ^を**に変換
    expression = re.sub(r'(?<=[a-zA-Z])(?=\d)', '**', expression)  # 文字と数字の間
    expression = re.sub(r'(?<=[)])(?=\d)', '**', expression)  # 括弧と数字の間
    return expression

def sort_expression(expression):
    # 式中に含まれる変数を取得
    variables = sorted(expression.free_symbols, key=lambda var: str(var))
    
    # 式が変数を含まない場合、そのまま返す
    if not variables:
        return expression

    terms = expression.as_ordered_terms()
    
    def get_sort_key(term):
        # 変数がある場合のみ多項式を作成
        if term.free_symbols:
            return (sp.Poly(term, *variables).total_degree(), term.as_coefficients_dict().keys())
        else:
            return (0, term.as_coefficients_dict().keys())  # 定数項の場合

    # キーに基づいて項をソート
    sorted_terms = sorted(terms, key=get_sort_key)
    
    # ソートされた項を加算して新しい式を作成
    sorted_expr = sp.Add(*sorted_terms)
    return sorted_expr

def format_expression(expression):
    expanded_expr = sp.expand(sp.sympify(expression))  # 展開
    simplified_expr = sp.simplify(expanded_expr)  # 簡略化
    sorted_expr = sort_expression(simplified_expr)
    formatted_expr = str(sorted_expr).replace('**', '^').replace('*', '')
    return formatted_expr

def format_equation(left_expr, right_expr):
    left_minus_right_expr = sp.simplify(left_expr - right_expr)  # 左辺と右辺の差を簡略化
    formatted_expr = format_expression(left_minus_right_expr)
    return f"{formatted_expr} = 0"


class TimeoutException(Exception):
    pass

def solve_equation(eq, var, result_container):
    result_container.append(sp.solve(eq, var))

def plot_graph(left_expr, right_expr, var1, var2, x_min=-5, x_max=5):
    # 先に計算
    left_expr = sp.simplify(left_expr)
    right_expr = sp.simplify(right_expr)
    print(left_expr)
    print(right_expr)

    # 変数の範囲を設定
    x_vals = np.linspace(x_min, x_max, 50)  # val1 (x) の範囲を50個の値に分割

    # 端に余分を持たせる割合を設定
    margin_rate = 0.08
    
    # val1 に対する val2 の値を計算
    y_vals = []
    
    for x in x_vals:
        y_vals_at_x = sp.solve(left_expr.subs(var1, x) - right_expr, var2)
        # 実数の解を数値に変換しリストに追加
        y_vals.extend([float(sol.evalf()) for sol in y_vals_at_x if sol.is_real])
    
    # 解が存在しない場合のエラーハンドリング
    if not y_vals:
        return f"{x_min}<={var1}<={x_max}の範囲内ではグラフを描画できません。"

    # y_vals の最小値と最大値を取得
    y_min = min(y_vals)
    y_max = max(y_vals)

    # 5%の余裕を追加
    y_margin = margin_rate * (y_max - y_min)
    y_min -= y_margin
    y_max += y_margin

    x_margin = margin_rate * (x_max - x_min)
    x_min -= x_margin
    x_max += x_margin

    print(f"最小値: {y_min}, 最大値: {y_max}")
    
    # タイトルを指定
    graph_title = format_equation(left_expr, right_expr)
    graph_title = change_I_and_i(graph_title)

    # グラフを描画するための範囲を設定
    x_vals_for_plot = np.linspace(x_min, x_max, 400)
    y_vals_for_plot = np.linspace(y_min, y_max, 400)
    X, Y = np.meshgrid(x_vals_for_plot, y_vals_for_plot)

    # 左辺と右辺の差を計算
    Z = sp.lambdify((var1, var2), left_expr - right_expr, 'numpy')(X, Y)

    # グラフの設定と描画
    plt.figure(figsize=(8, 6))  # 4:3のアスペクト比で図を作成
    plt.contour(X, Y, Z, levels=[0], colors='blue')  # 等高線を描画
    plt.title(graph_title)
    plt.xlabel(var1)
    plt.ylabel(var2)
    plt.grid()
    plt.axhline(0, color='black', linewidth=0.5, ls='--')
    plt.axvline(0, color='black', linewidth=0.5, ls='--')
    plt.xlim([x_min, x_max])  # val1 (x) の範囲
    plt.ylim([y_min, y_max])  # val2 (y) の範囲を調整

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
        # カンマで区切って部分を取得
        expression = clean_expression(expression)
        parts = [part.strip() for part in expression.split(',')]
        expression = parts[0]

        # グラフ表示用のxの最小値、最大値をあらかじめ指定
        var1_min = -5
        var1_max = 5

        if (len(parts) == 3):
            try:
                num1 = float(parts[1])
                num2 = float(parts[2])
                var1_min = min(num1, num2)
                var1_max = max(num1, num2)
            except Exception as e:
                print(e)
                pass

        expression = add_spaces(expression)
        expression = change_I_and_i(expression)
        expression = add_multiplication_sign(expression)
        expression = add_exponentiation_sign(expression)

        equal_sign_count = expression.count('=')

        if equal_sign_count == 1:
            left_side, right_side = expression.split('=')
            left_expr = sp.sympify(left_side.strip())
            right_expr = sp.sympify(right_side.strip())

            # 変数の取得
            variables = list(left_expr.free_symbols.union(right_expr.free_symbols))
            eq = sp.Eq(left_expr - right_expr, 0)

            try:
                # 結果を格納するためのリスト
                results = []
                threads = []

                # 変数ごとにスレッドを作成
                for var in variables:
                    thread = threading.Thread(target=solve_equation, args=(eq, var, results))
                    threads.append(thread)
                    thread.start()

                # スレッドの完了を待つ
                for thread in threads:
                    thread.join(timeout=10)  # 10秒待機
                    if thread.is_alive():  # スレッドがまだ動いている場合
                        print("解を求めるのに時間がかかりすぎました。")
                        raise TimeoutException("解を求めるのに時間がかかりすぎました。")

                # 解の表示形式を調整
                result = ""
                for var, sols in zip(variables, results):
                    if isinstance(sols, list):
                        for sol in sols:
                            result += f"{var} = {sol}\n"
                    else:
                        result += f"{var} = {sols}\n"

                result_str = result.strip() if result else "解なし"  # 解がない場合の処理
                result_str = str(result_str).replace('**', '^').replace('*', '')  # 形式を整形
                result_str = change_I_and_i(result_str)

            except TimeoutException as e:
                print("解を求めるのに時間がかかりすぎました。")
                result_str = "解を求めるのに時間がかかりすぎました。"
            except Exception as e:
                print(f"エラー: {e}")
                result_str = "解を求める際にエラーが発生しました。"
            print(len(variables))
            if len (variables) != 2:
                    return result_str
            else:
                var1, var2 = sorted(variables, key=lambda v: str(v))  # アルファベット順でソート
                image_path = plot_graph(left_expr, right_expr, str(var1), str(var2), x_min=var1_min, x_max=var1_max)  # グラフを描画
                if image_path == f"{var1_min}<={var1}<={var1_max}の範囲内ではグラフを描画できません。":
                    return result_str + "\n" + image_path
                else:
                    return result_str, image_path

        elif equal_sign_count > 1:
            return "方程式には等号 (=) をちょうど1個含めてください！"
        else:
            expanded_expr = sp.expand(sp.sympify(expression))  # 展開
            simplified_expr = sp.simplify(expanded_expr)  # 簡略化
            simplified_expr_str = str(simplified_expr).replace('**', '^').replace('*', '')  # 形式を整形
            result_str = change_I_and_i(simplified_expr_str)

            return f"{result_str}"

    except (sp.SympifyError, TypeError) as e:
        print(f"SymPy error: {e}")
        return "数式を正しく入力してください！"


def delete_image_after_delay(image_path, delay=300):  # デフォルトは300秒（5分間）
    time.sleep(delay)
    if os.path.exists(image_path):
        os.remove(image_path)
        print(f"画像ファイルが削除されました: {image_path}")

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    try:
        response = simplify_or_solve(user_message)
        if isinstance(response, tuple) and len(response) == 2:
            result_str, image_path = response
            image_url = f"https://manabu-hub-calc.onrender.com/static/{os.path.basename(image_path)}"
            
            # LINE APIクライアントの作成
            line_bot_api = MessagingApi(ApiClient(configuration))
            
            # 画像メッセージとテキストメッセージを同時に送信
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        ImageMessage(original_content_url=image_url, preview_image_url=image_url),
                        TextMessage(text=result_str)
                    ]
                )
            )
            print("画像とテキストを同時に送信:", image_path)

            # 画像送信後に別スレッドで削除処理を開始
            threading.Thread(target=delete_image_after_delay, args=(image_path,)).start()
        else:
            result_str = response
            # ここで解のテキストを送信
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=result_str)]
                    )
                )
    except Exception as e:
        print(f"Error: {e}")
        response = "申し訳ございません。エラーが発生したようです。もう一度試しても正常に作動しなければ、お手数お掛けしますがまなぶHUBの公式LINEまでご連絡ください。"
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)]
                )
            )


if __name__ == "__main__":
    port = int(os.environ.get("PORT"))
    app.run(host='0.0.0.0', port=port)