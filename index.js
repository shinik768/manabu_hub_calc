/*
const express = require('express');
const { Client, middleware } = require('@line/bot-sdk');
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

// JSONボディを解析するミドルウェアを最初に追加
app.use(express.json());

// LINEミドルウェアを追加
app.use(middleware(config));

app.get('/', (req, res) => {
    res.send('<p>Hello, World!</p>');
});

app.post('/callback', (req, res) => {
    console.log('Received a callback:', req.body); // リクエストボディをログに出力
    Promise
        .all(req.body.events.map(handleEvent))
        .then((result) => res.json(result))
        .catch((err) => {
            console.error(err);
            res.status(500).end();
        });
});

async function handleEvent(event) {
    if (event.type !== 'message' || event.message.type !== 'text') {
        return Promise.resolve(null);
    }

    const userMessage = event.message.text;

    // OpenAIのAPIを使用して応答を生成
    const completion = await openai.completions.create({
        model: 'text-davinci-003',
        prompt: `Q: ${userMessage}`,
        max_tokens: 150
    });

    const botReply = completion.choices[0].text.trim();

    // LINEに応答を送信
    const message = { type: 'text', text: botReply };
    return client.replyMessage(event.replyToken, message);
}

// エラーハンドリング
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
*/

const express = require("express");
const line = require("@line/bot-sdk");
const ngrok = require("ngrok");
require("dotenv").config();

const config = {
    channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN,
    channelSecret: process.env.LINE_CHANNEL_SECRET
};

const app = express();

const client = new line.messagingApi.MessagingApiClient({
  channelAccessToken: config.channelAccessToken,
});

app.use("/webhook", line.middleware(config));
app.post("/webhook", (req, res) => {
  Promise.all(req.body.events.map(handleEvent)).then((result) =>
    res.json(result)
  );
});

app.get("/", (req, res) => {
  res.send("LINE Bot is running.");
});  

function handleEvent(event) {
  if (event.type !== "message" || event.message.type !== "text") {
    return Promise.resolve(null);
  }

  return client.replyMessage({
    replyToken: event.replyToken,
    messages: [
      {
        type: "text",
        text: event.message.text,
      },
    ],
  });
}

const port = process.env.PORT || 3000;
app.listen(port, async () => {
  try {
    const ngrokUrl = await ngrok.connect(port);
    console.log(`Ngrok URL: ${ngrokUrl}/webhook`);
  } catch (error) {
    console.error("Error while connecting with ngrok:", error);
  }
});