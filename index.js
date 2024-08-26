const express = require('express');
const { Client, middleware, TextMessage } = require('@line/bot-sdk');
const OpenAI = require('openai');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

// LINE Messaging API設定
const config = {
    channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN,
    channelSecret: process.env.LINE_CHANNEL_SECRET
};

const client = new Client(config);

// OpenAI API設定
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

// ミドルウェアの設定
app.use(middleware(config));
app.use(express.json()); // JSONボディを解析するためのミドルウェア

// ホームエンドポイント
app.get('/', (req, res) => {
    console.log('Access Token:', process.env.LINE_CHANNEL_ACCESS_TOKEN);
    console.log('Channel Secret:', process.env.LINE_CHANNEL_SECRET);
    res.send('<p>Hello, World!</p>');
});

// コールバックエンドポイント
app.post('/callback', (req, res) => {
    console.log('Headers:', req.headers); // 追加
    const signature = req.headers['x-line-signature'];
    console.log('Received a callback:', req.body); // 受け取ったリクエストをログに出力
    console.log('Signature:', signature);
    Promise
        .all(req.body.events.map(handleEvent))
        .then((result) => res.json(result))
        .catch((err) => {
            console.error(err);
            res.status(500).end();
    });
});

// イベントハンドラ
async function handleEvent(event) {
    if (event.type !== 'message' || event.message.type !== 'text') {
        return Promise.resolve(null);
    }

    const userMessage = event.message.text;

    try {
        // OpenAIのAPIを使用して応答を生成
        const completion = await openai.completions.create({
            model: 'text-davinci-003',  // engineからmodelに変更
            prompt: `Q: ${userMessage}`,
            max_tokens: 150
        });

        const botReply = completion.choices[0].text.trim();

        // LINEに応答を送信
        const message = { type: 'text', text: botReply };
        return client.replyMessage(event.replyToken, message);
    } catch (error) {
        console.error('Error generating response:', error);
        throw error;  // エラーを再スロー
    }
}

// エラーハンドリング
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

// サーバーの起動
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
