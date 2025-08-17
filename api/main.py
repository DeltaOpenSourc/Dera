import os
import requests
from flask import Flask, Response, request, jsonify

TOKEN = os.getenv('TOKEN')

if not TOKEN:
    raise ValueError("Bot token is not set in environment variables!")

app = Flask(__name__)

def parse_message(message):
    if "message" not in message or "text" not in message["message"]:
        return None, None  

    chat_id = message["message"]["chat"]["id"]
    txt = message["message"]["text"]
    return chat_id, txt

@app.route('/setwebhook', methods=['POST','GET'])
def setwebhook():
    webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={os.environ.get('VERCEL_URL')}/webhook&allowed_updates=%5B%22message%22,%22callback_query%22%5D"
    response = requests.get(webhook_url)
    
    if response.status_code == 200:
        return "Webhook successfully set", 200
    else:
        return f"Error setting webhook: {response.text}", response.status_code
    return "Vercel URL not found", 400


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



def tel_send_message_not_markup(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print("Ошибка отправки сообщения:", response.text)

    return response


def delete_message(chat_id, message_id):
    """ Удаление сообщения с кнопками """
 
    url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage?chat_id={chat_id}&message_id={message_id}"
    response = requests.post(url)
    print(f"Удаление сообщения {message_id}: {response.status_code}, {response.text}") 
    if response.status_code != 200:
        print("Ошибка удаления сообщения:", response.text)    

user_states = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    msg = request.get_json()
    print("Получен вебхук:", msg)
    if "callback_query" in msg:
        callback = msg["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        callback_data = callback["data"]
        print(f"Нажата кнопка. Удаляю сообщение {message_id} из чата {chat_id}")

        delete_message(chat_id, message_id)

        if callback_data == "deepSeek":
            tel_send_message_not_markup(chat_id, "Вы выбрали диалог с ИИ. Как я могу помочь вам?")
            user_states[chat_id] = 'awating_response'
            return jsonify({"status": "message_sent"}), 200
        

        return jsonify({"status": "deleted"}), 200
    
       
    

    chat_id, txt = parse_message(msg)
    if chat_id is None or txt is None:
        return jsonify({"status": "ignored"}), 200
    
    if chat_id in user_states and user_states[chat_id] == "awaiting_response":
        tel_send_message(chat_id, f"Обрабатываю ваш запрос: {txt}")
        user_states[chat_id] = None 
    else:
        pass

    if txt.lower() == "/start":
        tel_send_message(chat_id, 
            "🎵 Добро пожаловать в наш уникальный музыкальный мир! "
            "Здесь вас ждут любимые треки и вдохновляющие клипы. 🎶\n\n"
            "✨ Мечтаете о персональной композиции? "
            "Закажите эксклюзивное музыкальное произведение, созданное специально для вас! 🎼\n\n"
            "🤖 Используйте возможности искусственного интеллекта для творческих запросов и новых идей. 🚀"
        ),
        

    return Response('ok', status=200)

@app.route("/", methods=['GET'])
def index():
    return "<h1>Telegram Bot Webhook is Running</h1>"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
