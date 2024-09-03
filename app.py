from tools.calc_manager import simplify_or_solve

import os
import time
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

# LINE API用の設定を取得
configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # リクエストをハンドラで処理
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

def delete_image_after_delay(image_path, delay=300):  # デフォルトは300秒（5分間）
    time.sleep(delay)  # 指定された時間待機
    if os.path.exists(image_path):
        os.remove(image_path)
        print(f"画像ファイルが削除されました: {image_path}")

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    try:
        response = simplify_or_solve(user_message)  # ユーザーからのメッセージを処理
        # 結果がテキスト、画像の両方であれば、両方とも出力
        if isinstance(response, tuple) and len(response) == 2:
            results_str, image_path = response
            image_url = f"https://manabu-hub-calc.onrender.com/static/{os.path.basename(image_path)}"
            
            # LINE APIクライアントの作成
            line_bot_api = MessagingApi(ApiClient(configuration))
            
            # 画像メッセージとテキストメッセージを同時に送信
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=result_str) for result_str in results_str
                    ] + [
                        ImageMessage(original_content_url=image_url, preview_image_url=image_url)
                    ]
                )
            )
            print("画像とテキストを同時に送信:", image_path)

            # 画像送信後に別スレッドで削除処理を開始
            threading.Thread(target=delete_image_after_delay, args=(image_path,)).start()
        # 結果がテキストだけであればテキストのみを出力
        else:
            results_str = response
            # ここで解のテキストを送信
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text=result_str) for result_str in results_str
                        ]
                    )
                )
    except Exception as e:
        print(f"Error: {e}")
        response = "申し訳ございません。エラーが発生したようです。もう一度試しても正常に動作しなければ、お手数お掛けしますがまなぶHUBの公式LINEまでご連絡ください。"
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)]
                )
            )


if __name__ == "__main__":
    port = int(os.environ.get("PORT"))  # ポート番号を環境変数から取得
    app.run(host='0.0.0.0', port=port)  # Flaskアプリを起動