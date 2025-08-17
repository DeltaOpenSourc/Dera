from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, Update
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
import aiohttp
from aiohttp import web
import os

TOKEN = '8283069945:AAGE67y1hIfmClH2Vtf6rLKRkzDMUiwqRIE'

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def CreateDB():
    query = """
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        conditions TEXT NOT NULL
    );
    """
    async with aiosqlite.connect("services.db") as db:
        await db.execute(query)
        await db.commit()

async def get_cards():
    async with aiosqlite.connect("services.db") as db:
        cursor = await db.execute("SELECT id, name FROM cards")
        cards = await cursor.fetchall()
        await cursor.close()
    return cards

async def cards_keyboard():
    cards = await get_cards()
    kb_builder = InlineKeyboardBuilder()
    for card_id, card_name in cards:
        kb_builder.button(text=card_name, callback_data=f"card_{card_id}")
    kb_builder.adjust(1)
    return kb_builder.as_markup()

class Form(StatesGroup):
    waiting_for_service_choice = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()
    waiting_for_inn = State()
    waiting_for_comment = State()

    partner_name = State()
    partner_city = State()
    partner_experience = State()
    partner_telegram = State()

    invoice_valuta = State()
    invoice_strana = State()
    invoice_summa = State()
    invoice_screen = State()
    invoice_comm = State()

    strana_other = State()
    strana_name = State()
    strana_telegram = State()
    strana_comm = State()
    strana_fer = State()
    strana_sv = State()
    strana_strana = State()

    manager = State()

    admin_waiting_for_country_name = State()
    admin_waiting_for_country_conditions = State()

MAIN_MENU_BUTTONS = [
    ("Оформить карту", "menu_card"),
    ("Оплатить инвойс", "menu_invoice"),
    ("Задать вопрос", "menu_question"),
    ("О нас", "menu_about"),
    ("Стать партнёром", "menu_partner"),
]

MAIN_CARD_BUTTONS = [
    ("🇹🇷 Турция", "strana_turcian"),
    ("🇦🇪 ОАЭ", "strana_oae"),
    ("🇹🇯 Таджикистан", "strana_tadzhikistan"),
    ("Другая", "strana_other"),
]

MAIN_FEART_BUTTONS = [
    ("Оставить заявку", "zayvka"),
]

MAIN_ADMIN_BUTTONS = [
    ("Добавить страну-карту", "st_create"),
    ("Удалить страну-карту", "st_delete"),
]

def main_menu_keyboard():
    kb_builder = InlineKeyboardBuilder()
    for text, cb_data in MAIN_MENU_BUTTONS:
        kb_builder.button(text=text, callback_data=cb_data)
    kb_builder.adjust(1)
    return kb_builder.as_markup()

def main_admin_keyboard():
    kb_builder = InlineKeyboardBuilder()
    for text, cb_data in MAIN_ADMIN_BUTTONS:
        kb_builder.button(text=text, callback_data=cb_data)
    kb_builder.adjust(1)
    return kb_builder.as_markup()

def main_feart_keyboard():
    kb_builder = InlineKeyboardBuilder()
    for text, cb_data in MAIN_FEART_BUTTONS:
        kb_builder.button(text=text, callback_data=cb_data)
    kb_builder.adjust(1)
    return kb_builder.as_markup()

def main_card_keyboard():
    kb_builder = InlineKeyboardBuilder()
    for text, cb_data in MAIN_CARD_BUTTONS:
        kb_builder.button(text=text, callback_data=cb_data)
    kb_builder.adjust(1)
    return kb_builder.as_markup()

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    kb = main_menu_keyboard()
    await CreateDB()
    await message.answer(
        "👋 Приветствуем в PaySecure — вашем личном помощнике в мире финансов.\n\n Здесь вы можете:\n💱 Переводить деньги между странами\n  💳 Получать карты для оплаты\n  📄 Оплачивать инвойсы в любых валютах Быстро\n\n Надёжно. Без лишних вопросов.  \n\nВыберите нужную функцию ниже 👇",
        reply_markup=kb,
    )
    await state.clear()

admin_ids = [7839682983]

@dp.message(Command(commands=["admin"]))
async def admin_add_card(message: Message):
    if message.from_user.id not in admin_ids:
        await message.answer("У вас нет доступа к этой команде.")
        return

    await message.answer(
        "Выберите действие:",
        reply_markup=main_admin_keyboard()
    )

@dp.callback_query(F.data.startswith("st_"))
async def process_admin_callback(call: CallbackQuery, state: FSMContext):
    action = call.data[len("st_"):]

    if action == "create":
        await call.message.answer("Введите название новой страны-карты:")
        await state.set_state(Form.admin_waiting_for_country_name)

    elif action == "delete":
        cards = await get_cards()
        if not cards:
            await call.message.answer("Нет стран для удаления.")
            await call.answer()
            return

        kb_builder = InlineKeyboardBuilder()
        for card_id, card_name in cards:
            kb_builder.button(text=card_name, callback_data=f"admin_delete_{card_id}")
        kb_builder.adjust(1)
        await call.message.answer("Выберите страну для удаления:", reply_markup=kb_builder.as_markup())

    await call.answer()

@dp.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_card_callback(call: CallbackQuery):
    card_id_str = call.data[len("admin_delete_"):]
    card_id = int(card_id_str)

    async with aiosqlite.connect("services.db") as db:
        cursor = await db.execute("SELECT name FROM cards WHERE id = ?", (card_id,))
        row = await cursor.fetchone()
        await cursor.close()
        card_name = row[0]

        await db.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        await db.commit()

    await call.message.edit_text(f"Страна-карта '{card_name}' успешно удалена.")
    await call.answer()

@dp.message(Form.admin_waiting_for_country_name)
async def admin_country_name_entered(message: Message, state: FSMContext):
    country_name = message.text.strip()
    await state.update_data(admin_country_name=country_name)
    await message.answer("Введите условия для страны-карты:")
    await state.set_state(Form.admin_waiting_for_country_conditions)

@dp.message(Form.admin_waiting_for_country_conditions)
async def admin_country_conditions_entered(message: Message, state: FSMContext):
    conditions = message.text.strip()
    data = await state.get_data()
    country_name = data.get("admin_country_name")

    async with aiosqlite.connect("services.db") as db:
        await db.execute(
            "INSERT INTO cards (name, conditions) VALUES (?, ?)",
            (country_name, conditions)
        )
        await db.commit()

    await message.answer(f"Страна-карта '{country_name}' успешно добавлена.")
    await state.clear()

@dp.callback_query(F.data.startswith("menu_"))
async def process_menu_callback(call: CallbackQuery, state: FSMContext):
    action = call.data[len("menu_"):]

    if action == "card":
        cards_create = await cards_keyboard()
        await call.message.answer("Выберите страну:", reply_markup=cards_create)

    elif action == "invoice":
        await call.message.answer("Пожалуйста, введите данные для оплаты инвойсов.\n1. Валюта:")
        await state.set_state(Form.invoice_valuta)

    elif action == "question":
        await call.message.answer("Задайте ваш вопрос:")
        await state.set_state(Form.manager)

    elif action == "about":
        await call.message.answer(
            "PaySecure — ваш надёжный партнёр в мире финтеха.\n\n"
            "Оформляем карты, помогаем с оплатой международных инвойсов.\n\n"
            "Контакт: @Paysecure1\n"
            "Email: Paysecure2025@gmail.com"
        )

    elif action == "partner":
        await call.message.answer("Пожалуйста, введите данные для регистрации партнёра.\n1. Имя:")
        await state.set_state(Form.partner_name)
    await call.answer()

@dp.callback_query(F.data.startswith("card_"))
async def process_strana_callback(call: CallbackQuery, state: FSMContext):
    country = call.data[len("card_"):]
    heart = main_feart_keyboard()
    async with aiosqlite.connect("services.db") as db:
        cursor = await db.execute("SELECT name FROM cards WHERE id = ?", (country,))
        row = await cursor.fetchone()
        await cursor.close()
        card_name = row[0]
    await state.update_data(selected_country=card_name)
    await call.message.answer(f"Вы выбрали карту {card_name}")

    async with aiosqlite.connect("services.db") as db_one:
        cursor_one = await db_one.execute("SELECT conditions FROM cards WHERE id = ?", (country,))
        row_one = await cursor_one.fetchone()
        await cursor_one.close()
        card_name_one = row_one[0]

    await call.message.answer(f"Условия карты: {card_name_one}", reply_markup=heart)
    await call.answer()

@dp.callback_query(F.data.startswith("zayvka"))
async def process_strana_callback(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    country = data.get("selected_country", "не выбрана")
    await call.message.answer(f"Вы выбрали страну: {country}")
    await call.message.answer(f"Введите имя:")
    await state.set_state(Form.strana_name)
    
    await call.answer()

@dp.message(Form.manager)
async def manager_sv(message: Message, state: FSMContext):
    await state.update_data(selected_manager=message.text)
    dataManager = await state.get_data()
    coun = dataManager.get("selected_manager", "не задан")
    await message.answer(f"Ваш вопрос: '{coun}' передан менеджеру ожидайте ответа!")
    await state.clear()

    payload = {
        "manager": dataManager["selected_manager"],
        "username": "@" + message.from_user.username or "не указан"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://nexthe-beta.vercel.app/api/manager", json=payload) as resp:
            if resp.status == 200:
                await message.answer("Отправлено...")
            else:
                await message.answer("Ошибка при отправке заявки на партнерство.")
    
@dp.message(Form.strana_name)
async def strana_telegram(message: Message, state: FSMContext):
    await state.update_data(selected_name=message.text)
    await message.answer(f"Введите telegram:")
    await state.set_state(Form.strana_telegram)

@dp.message(Form.strana_telegram)
async def strana_fer(message: Message, state: FSMContext):
    await state.update_data(selected_telegram=message.text)
    await message.answer(f"Введите страну:")
    await state.set_state(Form.strana_strana)

@dp.message(Form.strana_strana)
async def strana_fer(message: Message, state: FSMContext):
    await state.update_data(selected_strana=message.text)
    await message.answer(f"Введите способ связи:")
    await state.set_state(Form.strana_sv)

@dp.message(Form.strana_sv)
async def strana_sv(message: Message, state: FSMContext):
    await state.update_data(selected_sv=message.text)
    await message.answer(f"Введите комментарий:")
    await state.set_state(Form.strana_comm)

@dp.message(Form.strana_comm)
async def strana_comm(message: Message, state: FSMContext):
    await state.update_data(selected_comm=message.text)
    data = await state.get_data()
    await message.answer(
        "Ваша заявка отправлена!\n\n"
        f"Страна карты: {data['selected_country']}\n"
        f"Имя: {data['selected_name']}\n"
        f"Телеграмм: {data['selected_telegram']}\n"
        f"Страна: {data['selected_strana']}\n"
        f"Способ связи: {data['selected_sv']}\n"
        f"Комментарий: {data['selected_comm']}\n\n"
        "Мы свяжемся с вами в ближайшее время."
    )

    payload = {
        "strana_card": data["selected_country"],
        "name": data["selected_name"],
        "telegram": data["selected_telegram"],
        "strana": data['selected_strana'],
        "sv": data["selected_sv"],
        "comm": data["selected_comm"],
    }

    await state.clear()

    async with aiohttp.ClientSession() as session:
        async with session.post("https://nexthe-beta.vercel.app/api/karta", json=payload) as resp:
              await message.answer("Заявка успешно отправлена!")

@dp.message(Form.strana_other)
async def strana_other(message: Message, state: FSMContext):
    await state.update_data(selected_country=message.text)
    data = await state.get_data()
    country = data.get("selected_country", "не выбрана")
    await message.answer(f"Вы выбрали страну: {country}")
    heart = main_feart_keyboard()
    await message.answer("Условия карты:", reply_markup=heart)

@dp.callback_query(F.data.startswith("service_"))
async def process_service_choice(call: CallbackQuery, state: FSMContext):
    service_id = int(call.data[len("service_"):])
    await state.update_data(service_id=service_id)

    data = await state.get_data()
    country = data.get("selected_country", "не выбрана")

    await call.message.answer(f"Выбранная страна: {country}\nВведите ваше имя и фамилию:")
    await state.set_state(Form.waiting_for_name)
    await call.answer()

@dp.message(Form.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    country = data.get("selected_country", "не выбрана")
    await message.answer(f"Страна: {country}\nВведите ваш номер телефона:")
    await state.set_state(Form.waiting_for_phone)

@dp.message(Form.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    country = data.get("selected_country", "не выбрана")
    await message.answer(f"Страна: {country}\nВведите ваш email:")
    await state.set_state(Form.waiting_for_email)

@dp.message(Form.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    data = await state.get_data()
    country = data.get("selected_country", "не выбрана")
    await message.answer(f"Страна: {country}\nВведите ваш ИНН:")
    await state.set_state(Form.waiting_for_inn)

@dp.message(Form.waiting_for_inn)
async def process_inn(message: Message, state: FSMContext):
    await state.update_data(inn=message.text)
    data = await state.get_data()
    country = data.get("selected_country", "не выбрана")
    await message.answer(f"Страна: {country}\nВведите комментарий (если есть), или напишите 'нет':")
    await state.set_state(Form.waiting_for_comment)

@dp.message(Form.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    comment = message.text if message.text.lower() != "нет" else ""
    await state.update_data(comment=comment)
    await message.answer("Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время.")
    await state.clear()

@dp.message(Form.partner_name)
async def partner_name_handler(message: Message, state: FSMContext):
    await state.update_data(partner_name=message.text)
    await message.answer("2. Город:")
    await state.set_state(Form.partner_city)

@dp.message(Form.partner_city)
async def partner_city_handler(message: Message, state: FSMContext):
    await state.update_data(partner_city=message.text)
    await message.answer("3. Опыт:")
    await state.set_state(Form.partner_experience)

@dp.message(Form.partner_experience)
async def partner_experience_handler(message: Message, state: FSMContext):
    await state.update_data(partner_experience=message.text)
    await message.answer("4. Телеграмм:")
    await state.set_state(Form.partner_telegram)

@dp.message(Form.partner_telegram)
async def partner_telegram_handler(message: Message, state: FSMContext):
    await state.update_data(partner_telegram=message.text)
    data = await state.get_data()
    await message.answer(
        "Спасибо за регистрацию партнёра!\n\n"
        f"Имя: {data['partner_name']}\n"
        f"Город: {data['partner_city']}\n"
        f"Опыт: {data['partner_experience']}\n"
        f"Telegram: {data['partner_telegram']}\n\n"
        "Мы свяжемся с вами в ближайшее время."
    )

    payload = {
        "name": data["partner_name"],
        "city": data["partner_city"],
        "experience": data['partner_experience'],
        "telegram": data["partner_telegram"],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://nexthe-beta.vercel.app/api/der", json=payload) as resp:
            if resp.status == 200:
                await message.answer("Заявка на партнерство успешно отправлена!")
            else:
                await message.answer("Ошибка при отправке заявки на партнерство.")

    await state.clear()

@dp.message(Form.invoice_valuta)
async def process_invoice_valuta(message: Message, state: FSMContext):
    await state.update_data(valuta=message.text)
    await message.answer("2. Введите страну получателя:")
    await state.set_state(Form.invoice_strana)

@dp.message(Form.invoice_strana)
async def process_invoice_strana(message: Message, state: FSMContext):
    await state.update_data(strana=message.text)
    await message.answer("3. Введите сумму:")
    await state.set_state(Form.invoice_summa)

@dp.message(Form.invoice_summa)
async def process_invoice_summa(message: Message, state: FSMContext):
    await state.update_data(summa=message.text)
    await message.answer("4. Введите инвойс (можно отправить фотографию):")
    await state.set_state(Form.invoice_screen)

@dp.message(Form.invoice_screen)
async def process_invoice_screen(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id 
        file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        await state.update_data(screen=file_url)
        await message.answer("Инвойс принят. Теперь введите комментарий:")
        await state.set_state(Form.invoice_comm)
    else:
        await state.update_data(screen=message.text)
        await message.answer("Введите комментарий:")
        await state.set_state(Form.invoice_comm)

@dp.message(Form.invoice_comm)
async def process_invoice_comm(message: Message, state: FSMContext):
    await state.update_data(comm=message.text)
    data = await state.get_data()
    payload = {
        "valuta": data["valuta"],
        "strana": data["strana"],
        "summa": data['summa'],
        "screen": data["screen"],
        "comm": data["comm"],
        "username": "@" + message.from_user.username or "не указан"
    }

    await message.answer("Заявка на оплату инвойса отправлена, ожидайте!")
    await state.clear()

    async with aiohttp.ClientSession() as session:
        async with session.post("https://nexthe-beta.vercel.app/api/invoice", json=payload) as resp:
            if resp.status == 200:
                await message.answer("Инвойс успешно отправлен!")
            else:
                await message.answer("Ошибка при отправке инвойса.")

@dp.callback_query(F.data == "zayvka")
async def zayvka(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Форма заявки")
    await call.answer()

async def webhook(request):
    update = Update.to_object(await request.json())
    await dp.process_update(update)
    return web.Response()

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post('/webhook', webhook)
    web.run_app(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


