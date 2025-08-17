import os
import httpx
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

TOKEN = os.getenv('TOKEN')
TOKEN_DEEP_SEEK = os.getenv('TOKEN_DEEP_SEEK')

if not TOKEN or not TOKEN_DEEP_SEEK:
    raise ValueError("Bot token or Deep Seek token is not set in environment variables!")

app = FastAPI()

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=TOKEN_DEEP_SEEK,
)

user_states = {}
user_locks = {}

async def generate_response(text: str):
    try:
        completion = await client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[{"role": "user", "content": text}],
        )
        return completion.choices[0].message.content
    except Exception as e:
        print("Ошибка при генерации ответа:", e)
        return "Произошла ошибка при обработке вашего запроса."

@app.post('/webhook')
async def webhook(request: Request):
    msg = await request.json()
    print("Получен вебхук:", msg)

    chat_id = msg.get("message", {}).get("chat", {}).get("id")
    txt = msg.get("message", {}).get("text")

    if chat_id is None or txt is None:
        return JSONResponse(content={"status": "ignored"}, status_code=200)

    async with user_locks.setdefault(chat_id, asyncio.Lock()):
        if txt.lower() == "/start":
            await tel_send_message(chat_id, "Добро пожаловать!")
            return JSONResponse(content={"status": "ok"}, status_code=200)

        await tel_send_message(chat_id, "Обрабатываю ваш запрос...")
        response = await generate_response(txt)
        await tel_send_message(chat_id, response)

    return JSONResponse(content={"status": "ok"}, status_code=200)

async def tel_send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
    return response

@app.get("/")
async def index():
    return "<h1>Telegram Bot Webhook is Running</h1>"

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)), log_level="info")

