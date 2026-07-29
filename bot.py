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
    WebAppInfo
)

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8669209199:AAFnRG3FG4q0KpR7T-bk_THhpAhEltz_H7U"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== ХРАНИЛИЩЕ СДЕЛОК ====================
exchanges = {}

# ==================== ФУНКЦИИ ====================
def generate_code():
    """Генерирует 4-значный код"""
    return f"{random.randint(0, 9999):04d}"

def format_price(price):
    if price.is_integer():
        return f"${int(price)}"
    return f"${price:.2f}"

# ==================== КНОПКИ ====================
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
        resize_keyboard=True
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
    
    # Кнопка для открытия Web App
    web_app_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 Открыть приложение",
                web_app=WebAppInfo(url="https://ajl7oputm.github.io/AppTrade/")
            )],
            [InlineKeyboardButton(
                text="💬 Использовать чат",
                callback_data="use_chat"
            )]
        ]
    )
    
    await message.answer(
        "✨ *Добро пожаловать в Trade Bot!* ✨\n\n"
        "🤝 Здесь вы можете безопасно обмениваться подарками.\n\n"
        "📌 *Как это работает:*\n"
        "1️⃣ Нажмите «Создать сделку» и загрузите ссылку\n"
        "2️⃣ Получите уникальный номер и пароль\n"
        "3️⃣ Покупатель вводит данные и подключается\n"
        "4️⃣ Через 1 минуту сделка завершается ✅\n\n"
        "🔐 *Все сделки защищены!*\n\n"
        "📱 *Выберите способ взаимодействия:*",
        parse_mode="Markdown",
        reply_markup=web_app_button
    )

@dp.callback_query(lambda c: c.data == "use_chat")
async def process_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "💬 Используйте кнопки ниже для работы с ботом:",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("app"))
async def cmd_app(message: types.Message):
    web_app_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 Открыть приложение",
                web_app=WebAppInfo(url="https://ajl7oputm.github.io/AppTrade/")
            )]
        ]
    )
    
    await message.answer(
        "📱 *Trade Bot App*\n\n"
        "Нажмите кнопку, чтобы открыть полноценное приложение!",
        parse_mode="Markdown",
        reply_markup=web_app_button
    )

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активных операций.", reply_markup=get_main_keyboard())
        return
    await state.clear()
    await message.answer("✅ Операция отменена.", reply_markup=get_main_keyboard())

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if not exchanges:
        await message.answer("📭 Нет активных сделок.", reply_markup=get_main_keyboard())
        return
    
    text = "📋 *Активные сделки:*\n\n"
    for eid, data in exchanges.items():
        if data["status"] not in ["completed"]:
            text += f"└ #{eid} - {data['status']}\n"
    await message.answer(text, parse_mode="Markdown")

# ==================== СОЗДАНИЕ СДЕЛКИ ====================
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
        f"📌 *Номер:* `{exchange_id}`\n"
        f"🔑 *Пароль:* `{password}`\n\n"
        f"📎 Отправьте *ссылку на подарок*:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@dp.message(TradeStates.waiting_for_create_link)
async def process_create_link(message: types.Message, state: FSMContext):
    gift_link = message.text.strip()
    
    if not re.match(r'^https?://', gift_link):
        await message.answer("❌ Отправьте ссылку (http:// или https://)", parse_mode="Markdown")
        return
    
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id in exchanges:
        exchanges[exchange_id]["gift_link"] = gift_link
        exchanges[exchange_id]["status"] = "waiting_for_price"
    
    await state.set_state(TradeStates.waiting_for_create_price)
    await message.answer("💰 Укажите сумму (в долларах):", parse_mode="Markdown")

@dp.message(TradeStates.waiting_for_create_price)
async def process_create_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            await message.answer("❌ Сумма должна быть > 0")
            return
    except ValueError:
        await message.answer("❌ Введите число")
        return
    
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id in exchanges:
        exchanges[exchange_id]["price"] = price
        exchanges[exchange_id]["status"] = "waiting_for_buyer"
    
    price_str = format_price(price)
    
    await message.answer(
        f"✅ *Сделка создана!* 🎉\n\n"
        f"📋 Номер: `{exchange_id}`\n"
        f"🔑 Пароль: `{exchanges[exchange_id]['password']}`\n"
        f"💰 Сумма: {price_str}\n\n"
        f"⏳ Ожидайте покупателя...",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# ==================== ПОДКЛЮЧЕНИЕ ====================
@dp.message(lambda message: message.text == "🔗 Подключиться")
async def button_connect_exchange(message: types.Message, state: FSMContext):
    await state.set_state(TradeStates.waiting_for_exchange)
    await message.answer("🔍 Введите *номер сделки*:", parse_mode="Markdown")

@dp.message(TradeStates.waiting_for_exchange)
async def process_exchange_number(message: types.Message, state: FSMContext):
    exchange_id = message.text.strip()
    
    if exchange_id not in exchanges:
        await message.answer("❌ Сделка не найдена. Проверьте номер.")
        return
    
    if exchanges[exchange_id]["status"] == "completed":
        await message.answer("❌ Сделка уже завершена.")
        await state.clear()
        return
    
    await state.update_data(exchange_id=exchange_id)
    await state.set_state(TradeStates.waiting_for_password)
    await message.answer(f"🔑 Введите *пароль* для #{exchange_id}:", parse_mode="Markdown")

@dp.message(TradeStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    exchange_id = data.get('exchange_id')
    
    if exchange_id not in exchanges:
        await message.answer("❌ Сделка не найдена.")
        await state.clear()
        return
    
    if exchanges[exchange_id]["password"] != password:
        await message.answer("❌ Неверный пароль. Попробуйте снова.")
        return
    
    # Подключение
    exchanges[exchange_id]["buyer"] = message.from_user.id
    exchanges[exchange_id]["status"] = "active"
    
    price = exchanges[exchange_id]["price"]
    price_str = format_price(price)
    
    await message.answer(
        f"✅ *Подключение успешно!*\n\n"
        f"📋 Сделка #{exchange_id}\n"
        f"💰 Сумма: {price_str}\n\n"
        f"⏳ Ожидайте 1 минуту...",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Уведомление создателя
    creator_id = exchanges[exchange_id]["creator"]
    try:
        await bot.send_message(
            creator_id,
            f"🔔 Кто-то подключился к сделке #{exchange_id}!\n💰 {price_str}\n⏳ Через 1 минуту завершение."
        )
    except:
        pass
    
    await state.clear()
    
    # ⏳ Задержка 60 секунд
    await asyncio.sleep(60)
    
    if exchange_id not in exchanges or exchanges[exchange_id]["status"] != "active":
        return
    
    exchanges[exchange_id]["status"] = "completed"
    
    # Финальное сообщение
    try:
        await message.answer(
            f"✅ *Сделка завершена!* 🎉\n\n"
            f"📦 Отправьте подарок: @ValletTrade\n"
            f"📋 #{exchange_id} | {price_str}",
            parse_mode="Markdown"
        )
    except:
        pass
    
    try:
        await bot.send_message(
            creator_id,
            f"✅ Сделка #{exchange_id} завершена!\n📦 Получите подарок!"
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
                my_exchanges.append(eid)
    
    if not my_exchanges:
        await message.answer("📭 У вас нет активных сделок.", reply_markup=get_main_keyboard())
        return
    
    text = "📋 *Ваши сделки:*\n"
    for eid in my_exchanges:
        text += f"└ #{eid}\n"
    
    await message.answer(text, parse_mode="Markdown")

# ==================== КНОПКА ОТМЕНА ====================
@dp.message(lambda message: message.text == "❌ Отмена")
async def button_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активных операций.", reply_markup=get_main_keyboard())
        return
    await state.clear()
    await message.answer("✅ Отменено!", reply_markup=get_main_keyboard())

# ==================== ОСТАЛЬНЫЕ СООБЩЕНИЯ ====================
@dp.message()
async def handle_all_messages(message: types.Message, state: FSMContext):
    if await state.get_state() is None:
        await message.answer(
            "❓ Используйте кнопки ниже 👇",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "⏳ Следуйте инструкциям бота.",
            reply_markup=get_main_keyboard()
        )

# ==================== ЗАПУСК ====================
async def main():
    print("=" * 50)
    print("🤖 TRADE BOT ЗАПУЩЕН!")
    print("🔗 Web App: https://ajl7oputm.github.io/AppTrade/")
    print("📋 4-значный ID и пароль")
    print("⏳ 60 секунд на сделку")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
