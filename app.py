
from flask import Flask, request, abort
import os
import logging

app = Flask(__name__)

port = int(os.environ.get("PORT", 5000))

# ロギングの設定
logging.basicConfig(level=logging.ERROR)

@app.route('/')
def home():
    return "<p>Hello, World!</p>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)





