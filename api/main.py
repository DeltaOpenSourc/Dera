import os
import requests
from flask import Flask, Response, request, jsonify
from openai import OpenAI, AsyncOpenAI
import httpx

TOKEN = os.getenv('TOKEN')
TOKEN_DEEP_SEEK = os.getenv('TOKEN_DEEP_SEEK')

if not TOKEN:
    raise ValueError("Bot token is not set in environment variables!")

app = Flask(__name__)

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=TOKEN_DEEP_SEEK,
)

MAX_MESSAGE_LENGTH = 4096 

async def split_text(text, max_length=MAX_MESSAGE_LENGTH):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


async def generate_response(text: str):
    completion = await client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[{"role": "user", "content": text}],
    )
    return completion.choices[0].message.content

async def parse_message(message):
    if "message" not in message or "text" not in message["message"]:
        return None, None  

    chat_id = message["message"]["chat"]["id"]
    txt = message["message"]["text"]
    return chat_id, txt

@app.route('/setwebhook', methods=['POST', 'GET'])
def setwebhook():
    webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={os.environ.get('VERCEL_URL')}/webhook&allowed_updates=%5B%22message%22,%22callback_query%22%5D"
    response = requests.get(webhook_url)

async def tel_send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": reply_markup
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            print("Ошибка отправки сообщения:", response.text)

async def tel_send_message_not_markup(chat_id, text):
    await tel_send_message(chat_id, text)

async def delete_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage?chat_id={chat_id}&message_id={message_id}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        if response.status_code != 200:
            print("Ошибка удаления сообщения:", response.text)    

user_states = {}

@app.route('/webhook', methods=['POST'])
async def webhook():
    msg = request.get_json()
    print("Получен вебхук:", msg)

    if "callback_query" in msg:
        callback = msg["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        callback_data = callback["data"]

        await delete_message(chat_id, message_id)

        if callback_data == "deepSeek":
            await tel_send_message_not_markup(chat_id, "Вы выбрали диалог с ИИ. Как я могу помочь вам?")
            user_states[chat_id] = 'awaiting_response'
            return jsonify({"status": "message_sent"}), 200

        return jsonify({"status": "deleted"}), 200

    chat_id, txt = await parse_message(msg)
    if chat_id is None or txt is None:
        return jsonify({"status": "ignored"}), 200

    if chat_id in user_states and user_states[chat_id] == "awaiting_response":
        await tel_send_message_not_markup(chat_id, f"Обрабатываю ваш запрос: {txt}")
        neural_response = await generate_response(txt)  

        for part in await split_text(neural_response):
            await tel_send_message_not_markup(chat_id, part)

        user_states[chat_id] = None  
    elif txt.lower() == "/start":
        await tel_send_message(chat_id, 
            "🎵 Добро пожаловать в наш уникальный музыкальный мир! "
            "Здесь вас ждут любимые треки и вдохновляющие клипы. 🎶\n\n"
            "✨ Мечтаете о персональной композиции? "
            "Закажите эксклюзивное музыкальное произведение, созданное специально для вас! 🎼\n\n"
            "🤖 Используйте возможности искусственного интеллекта для творческих запросов и новых идей. 🚀"
        )

    return Response('ok', status=200)

@app.route("/", methods=['GET'])
def index():
    return "<h1>Telegram Bot Webhook is Running</h1>"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
