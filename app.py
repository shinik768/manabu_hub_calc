import os
from flask import Flask, abort, request
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# 環境変数からアクセストークンとシークレットを取得
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
configuration = Configuration(access_token=os.environ['LINE_CHANNEL_ACCESS_TOKEN'])

@app.route("/callback", methods=['POST'])
def callback():
    # X-Line-Signature ヘッダー値を取得
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    # Webhookボディを処理
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        # ユーザーのメッセージに応じたレスポンス
        if event.message.text == 'グー':
            msg = 'パー'
        elif event.message.text == 'チョキ':
            msg = 'グー'
        elif event.message.text == 'パー':
            msg = 'チョキ'
        else:
            msg = 'ごめんね。\nまだ他のメッセージには対応してないよ'

        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=msg)]
            )
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
