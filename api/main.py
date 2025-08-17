import os
import requests
import asyncio
from flask import Flask, Response, request, jsonify
from openai import AsyncOpenAI
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv('TOKEN')
TOKEN_DEEP_SEEK = os.getenv("TOKEN_DEEP_SEEK")

if not TOKEN:
    raise ValueError("Bot token is not set in environment variables!")

app = Flask(__name__)

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=TOKEN_DEEP_SEEK,
)

async def a_generate(text: str):
    completion = await client.chat.completions.create(
        model="deepseek/deepseek-r1-0528:free",
        messages=[{"role": "user", "content": text}],
    )
    return completion.choices[0].message.content

def parse_message(message):
    """ Парсим сообщение от Telegram API """
    if "message" not in message or "text" not in message["message"]:
        return None, None  

    chat_id = message["message"]["chat"]["id"]
    txt = message["message"]["text"]
    return chat_id, txt

@app.route('/setwebhook', methods=['POST', 'GET'])
def setwebhook():
    webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={os.environ.get('VERCEL_URL')}/webhook&allowed_updates=%5B%22message%22,%22callback_query%22%5D"
    response = requests.get(webhook_url)
    
    if response.status_code == 200:
        return "Webhook successfully set", 200
    else:
        return f"Error setting webhook: {response.text}", response.status_code

def tel_send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "Открыть Муз Чат", 
                        "web_app": {"url": "https://getstarthealth.github.io/Obmen/"}
                    },
                    {
                        "text": "Диалог с ИИ", 
                        "callback_data": "deepSeek"
                    }
                ]
            ]
        }
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print("Ошибка отправки сообщения:", response.text)

    return response

@app.route('/webhook', methods=['POST'])
def webhook():
    """ Обработка входящих сообщений от Telegram API """
    msg = request.get_json()

    if "callback_query" in msg:
        callback = msg["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]

        if data == "deepSeek":
            # Обработка нажатия кнопки "Диалог с ИИ"
            tel_send_message(chat_id, "Диалог открыт, задавайте запрос:")
            return jsonify({"status": "dialog opened"}), 200

    chat_id, txt = parse_message(msg)
    if chat_id is None or txt is None:
        return jsonify({"status": "ignored"}), 200

    if txt.lower() == "/start":
        tel_send_message(chat_id, 
            "🎵 Добро пожаловать в наш уникальный музыкальный мир! "
            "Здесь вас ждут любимые треки и вдохновляющие клипы. 🎶\n\n"
            "✨ Мечтаете о персональной композиции? "
            "Закажите эксклюзивное музыкальное произведение, созданное специально для вас! 🎼\n\n"
            "🤖 Используйте возможности искусственного интеллекта для творческих запросов и новых идей. 🚀"
        )
    
    if "диалог открыт, задавайте запрос" in txt.lower():

        response_text = asyncio.run(a_generate(txt))
        tel_send_message(chat_id, response_text)

    return Response('ok', status=200)

@app.route("/", methods=['GET'])
def index():
    return "<h1>Telegram Bot Webhook is Running</h1>"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
